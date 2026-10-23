// ocr-pdf-core: the native OCR program. The desktop app starts one per file
// and reads its progress from stdout, one JSON message per line:
//
//   ocr-pdf-core run --input IN --output OUT --languages rus+eng
//                    [--force] [--deskew] [--tessdata DIR] [--gs PROGRAM]
//                    [--jobs N]
//   ocr-pdf-core expand --extensions .pdf,.png --skip-suffix _ocr PATH...
//
// The messages are the same ones the web version's workers send, see
// web/js/engine-web.js.

#include <algorithm>
#include <atomic>
#include <cstdio>
#include <exception>
#include <filesystem>
#include <fstream>
#include <mutex>
#include <random>
#include <thread>

#include "ocr.hpp"
#include "pdfa.hpp"
#include "process.hpp"

namespace fs = std::filesystem;
using namespace ocr;

namespace {

#ifdef _WIN32
const char EXE_SUFFIX[] = ".exe";
#else
const char EXE_SUFFIX[] = "";
#endif
const char GS_NAME[] = "ocr-pdf-gs";
const char USAGE[] =
    "usage: ocr-pdf-core run --input IN --output OUT --languages LANGS\n"
    "           [--force] [--deskew] [--tessdata DIR] [--gs PROGRAM]\n"
    "           [--jobs N]\n"
    "       ocr-pdf-core expand --extensions EXTS --skip-suffix S PATH...\n";

struct Job {
    std::string input, output, tessdata, gs;
    Options options;
    int jobs = 1;
};

std::mutex stdout_mutex;

std::string json(const std::string &text)
{
    std::string out = "\"";
    for (unsigned char c : text) {
        if (c == '"' || c == '\\') {
            out += '\\';
            out += char(c);
        } else if (c < 0x20) {
            char escaped[8];
            std::snprintf(escaped, sizeof escaped, "\\u%04x", c);
            out += escaped;
        } else {
            out += char(c);
        }
    }
    return out + "\"";
}

void emit(const std::string &fields)
{
    std::lock_guard<std::mutex> lock(stdout_mutex);
    std::printf("{%s}\n", fields.c_str());
    std::fflush(stdout);
}

void progress(const std::string &stage, int done, int total)
{
    emit("\"event\":\"progress\",\"stage\":" + json(stage) +
         ",\"done\":" + std::to_string(done) +
         ",\"total\":" + std::to_string(total));
}

void warn(const std::string &message)
{
    emit("\"event\":\"log\",\"level\":\"warning\",\"msg\":" + json(message));
}

// The folder for the job's intermediate files, removed afterwards
class WorkDir {
public:
    WorkDir()
    {
        std::random_device random;
        path_ = fs::temp_directory_path() /
                ("ocr-pdf-" + std::to_string(random()));
        fs::create_directories(path_);
    }
    ~WorkDir()
    {
        std::error_code ignored;
        fs::remove_all(path_, ignored);
    }
    std::string file(const std::string &name) const
    {
        return (path_ / name).u8string();
    }
    std::string utf8() const { return path_.u8string(); }

private:
    fs::path path_;
};

std::vector<PageResult> ocr_pages(const Context &ctx, const Input &input,
                                  const Job &job, const WorkDir &work)
{
    std::vector<PageResult> results(input.pages);
    std::atomic<int> next{0}, done{0};
    std::exception_ptr failure;
    std::mutex failure_mutex;

    auto work_on_pages = [&] {
        try {
            PageOcr ocr(ctx, input.pdf, job.tessdata, job.options);
            for (int page; (page = next++) < input.pages;) {
                results[page] = ocr.run(page, work.utf8());
                progress("ocr", ++done, input.pages);
            }
        } catch (...) {
            std::lock_guard<std::mutex> lock(failure_mutex);
            if (!failure)
                failure = std::current_exception();
            next = input.pages;
        }
    };

    std::vector<std::thread> threads;
    int count = std::clamp(job.jobs, 1, input.pages);
    for (int i = 1; i < count; i++)
        threads.emplace_back(work_on_pages);
    work_on_pages();
    for (std::thread &thread : threads)
        thread.join();

    if (failure)
        std::rethrow_exception(failure);
    return results;
}

// PDF/A when Ghostscript manages it, otherwise the plain PDF, like
// OCRmyPDF's output type "auto"
std::string make_pdfa(const std::string &pdf, const WorkDir &work,
                      const Job &job)
{
    progress("pdfa", 0, 1);
    std::string definitions = work.file("pdfa.ps");
    std::string out = work.file("pdfa.pdf");
    std::ofstream(fs::u8path(definitions)) << PDFA_DEFINITIONS;

    int code = run_program(job.gs, pdfa_args(definitions, pdf, out));
    std::error_code ec;
    auto size = fs::file_size(fs::u8path(out), ec);
    if (code == 0 && !ec && size > 0) {
        progress("pdfa", 1, 1);
        return out;
    }
    warn("Ghostscript could not make PDF/A (exit code " +
         std::to_string(code) + "), the result is a regular PDF");
    return pdf;
}

// Copied next to the output first, so the output is never half-written
void deliver(const std::string &result, const std::string &output)
{
    fs::path target = fs::u8path(output);
    fs::path part = target;
    part += ".part";

    std::error_code ec;
    fs::copy_file(fs::u8path(result), part,
                  fs::copy_options::overwrite_existing, ec);
    if (!ec)
        fs::rename(part, target, ec);
    if (ec) {
        std::error_code ignored;
        fs::remove(part, ignored);
        throw Error("output_access", output + ": " + ec.message());
    }
}

void run(const Job &job)
{
    WorkDir work;
    Context ctx;

    progress("scan", 0, 1);
    Input input = prepare(ctx, job.input, work.utf8());
    std::vector<PageResult> pages = ocr_pages(ctx, input, job, work);
    if (std::all_of(pages.begin(), pages.end(), [](const PageResult &page) {
            return page.action == OCR_SKIP;
        }))
        throw Error("has_text", "every page already has text");

    progress("save", 0, 1);
    std::string ocr_pdf = work.file("ocr.pdf");
    assemble(ctx, input.pdf, pages, ocr_pdf);
    deliver(make_pdfa(ocr_pdf, work, job), job.output);
    emit("\"event\":\"done\",\"output\":" + json(job.output));
}

Job parse_job(const std::vector<std::string> &args)
{
    Job job;
    job.tessdata = program_dir() + "/tessdata";
    job.gs = program_dir() + "/" + GS_NAME + EXE_SUFFIX;
    job.jobs = int(std::thread::hardware_concurrency());

    for (size_t i = 1; i < args.size(); i++) {
        const std::string &flag = args[i];
        bool has_value = i + 1 < args.size();
        if (flag == "--force")
            job.options.force = true;
        else if (flag == "--deskew")
            job.options.deskew = true;
        else if (flag == "--input" && has_value)
            job.input = args[++i];
        else if (flag == "--output" && has_value)
            job.output = args[++i];
        else if (flag == "--languages" && has_value)
            job.options.languages = args[++i];
        else if (flag == "--tessdata" && has_value)
            job.tessdata = args[++i];
        else if (flag == "--gs" && has_value)
            job.gs = args[++i];
        else if (flag == "--jobs" && has_value)
            job.jobs = std::stoi(args[++i]);
        else
            throw std::invalid_argument("unknown argument " + flag);
    }
    if (job.input.empty() || job.output.empty() ||
        job.options.languages.empty())
        throw std::invalid_argument("--input, --output and --languages "
                                    "are required");
    return job;
}

int run_command(const std::vector<std::string> &args)
{
    std::string kind = "other", detail;
    try {
        run(parse_job(args));
        return 0;
    } catch (const Error &e) {
        kind = e.kind();
        detail = e.what();
    } catch (const std::bad_alloc &e) {
        kind = "too_big";
        detail = e.what();
    } catch (const std::exception &e) {
        detail = e.what();
    }
    emit("\"event\":\"error\",\"kind\":" + json(kind) +
         ",\"detail\":" + json(detail));
    return 1;
}

// --- expand ------------------------------------------------------------------

std::vector<std::string> split(const std::string &text, char separator)
{
    std::vector<std::string> parts;
    size_t start = 0, end;
    while ((end = text.find(separator, start)) != std::string::npos) {
        parts.push_back(text.substr(start, end - start));
        start = end + 1;
    }
    parts.push_back(text.substr(start));
    return parts;
}

std::string lower(std::string text)
{
    std::transform(text.begin(), text.end(), text.begin(), [](char c) {
        return c >= 'A' && c <= 'Z' ? char(c - 'A' + 'a') : c;
    });
    return text;
}

struct Expand {
    std::vector<std::string> extensions;
    std::string skip_suffix;

    // Inside folders our own results are skipped, so dropping the same
    // folder again does not recognize them a second time
    bool wanted(const fs::path &file) const
    {
        std::string stem = file.stem().u8string();
        bool ours = stem.size() >= skip_suffix.size() &&
                    stem.compare(stem.size() - skip_suffix.size(),
                                 std::string::npos, skip_suffix) == 0;
        std::string ext = lower(file.extension().u8string());
        return !ours && std::find(extensions.begin(), extensions.end(),
                                  ext) != extensions.end();
    }

    void add_folder(const fs::path &folder,
                    std::vector<std::string> &found) const
    {
        std::vector<std::string> files;
        std::error_code ec;
        auto options = fs::directory_options::skip_permission_denied;
        for (fs::recursive_directory_iterator it(folder, options, ec), end;
             !ec && it != end; it.increment(ec))
            if (it->is_regular_file(ec) && wanted(it->path()))
                files.push_back(it->path().u8string());
        std::sort(files.begin(), files.end());
        found.insert(found.end(), files.begin(), files.end());
    }
};

// Folders become the matching files inside them; files stay as they are,
// and the app tells the user about those it cannot take
int expand_command(const std::vector<std::string> &args)
{
    Expand expand;
    std::vector<std::string> found;
    for (size_t i = 1; i < args.size(); i++) {
        bool has_value = i + 1 < args.size();
        if (args[i] == "--extensions" && has_value) {
            expand.extensions = split(lower(args[++i]), ',');
        } else if (args[i] == "--skip-suffix" && has_value) {
            expand.skip_suffix = args[++i];
        } else {
            std::error_code ec;
            fs::path path = fs::u8path(args[i]);
            if (fs::is_directory(path, ec))
                expand.add_folder(path, found);
            else if (fs::is_regular_file(path, ec))
                found.push_back(args[i]);
        }
    }

    std::string list;
    for (const std::string &file : found)
        list += (list.empty() ? "" : ",") + json(file);
    std::printf("[%s]\n", list.c_str());
    return 0;
}

} // namespace

int main(int argc, char **argv)
{
    std::vector<std::string> args(argv + 1, argv + argc);
    if (!args.empty() && args[0] == "run")
        return run_command(args);
    if (!args.empty() && args[0] == "expand")
        return expand_command(args);
    std::fputs(USAGE, stderr);
    return 2;
}
