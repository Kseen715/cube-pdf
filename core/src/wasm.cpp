// The WebAssembly face of the pipeline, used by web/js/worker.js. Files live
// in Emscripten's in-memory file system. Results are plain JavaScript
// objects; a failure comes back as {error, detail}, not as an exception.
//
// Each worker has its own instance of the module, so the one PageOcr kept
// here belongs to that worker.

#include <memory>
#include <new>

#include <emscripten/bind.h>
#include <emscripten/val.h>

#include "ocr.hpp"
#include "pdfa.hpp"

using emscripten::val;

namespace {

std::unique_ptr<ocr::PageOcr> page_ocr;

const ocr::Context &context()
{
    static ocr::Context ctx;
    return ctx;
}

val failure(const std::string &kind, const std::string &detail)
{
    val result = val::object();
    result.set("error", kind);
    result.set("detail", detail);
    return result;
}

template <class Work> val guarded(Work work)
{
    try {
        return work();
    } catch (const ocr::Error &e) {
        return failure(e.kind(), e.what());
    } catch (const std::bad_alloc &e) {
        return failure("too_big", e.what());
    } catch (const std::exception &e) {
        return failure("other", e.what());
    }
}

val prepare(std::string input, std::string workdir)
{
    return guarded([&] {
        ocr::Input in = ocr::prepare(context(), input, workdir);
        val result = val::object();
        result.set("pdf", in.pdf);
        result.set("pages", in.pages);
        return result;
    });
}

// options: {languages: 'rus+eng', force: bool, deskew: bool}
val start_pages(std::string pdf, std::string tessdata, val options)
{
    return guarded([&] {
        ocr::Options opts;
        opts.languages = options["languages"].as<std::string>();
        opts.force = options["force"].as<bool>();
        opts.deskew = options["deskew"].as<bool>();
        page_ocr.reset();
        page_ocr =
            std::make_unique<ocr::PageOcr>(context(), pdf, tessdata, opts);
        return val::object();
    });
}

val ocr_page(int page, std::string workdir)
{
    return guarded([&] {
        ocr::PageResult page_result = page_ocr->run(page, workdir);
        val result = val::object();
        result.set("action", int(page_result.action));
        result.set("rotate", page_result.rotate);
        result.set("layer", page_result.layer);
        return result;
    });
}

// pages: [{action, rotate, layer}], as ocr_page returned them
val assemble(std::string pdf, val pages, std::string out)
{
    return guarded([&] {
        std::vector<ocr::PageResult> results;
        for (int i = 0; i < pages["length"].as<int>(); i++) {
            val page = pages[i];
            results.push_back({ocr_action(page["action"].as<int>()),
                               page["rotate"].as<int>(),
                               page["layer"].as<std::string>()});
        }
        ocr::assemble(context(), pdf, results, out);
        return val::object();
    });
}

val pdfa_args(std::string definitions, std::string in, std::string out)
{
    val args = val::array();
    for (const std::string &arg : ocr::pdfa_args(definitions, in, out))
        args.call<void>("push", arg);
    return args;
}

std::string pdfa_definitions() { return ocr::PDFA_DEFINITIONS; }

} // namespace

EMSCRIPTEN_BINDINGS(ocr_core)
{
    emscripten::function("prepare", &prepare);
    emscripten::function("startPages", &start_pages);
    emscripten::function("ocrPage", &ocr_page);
    emscripten::function("assemble", &assemble);
    emscripten::function("pdfaArgs", &pdfa_args);
    emscripten::function("pdfaDefinitions", &pdfa_definitions);
}
