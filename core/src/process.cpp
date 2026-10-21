#include "process.hpp"

#ifdef _WIN32
#include <iterator>

#include <windows.h>
#else
#include <cerrno>
#include <csignal>
#include <limits.h>
#include <sys/prctl.h>
#include <sys/wait.h>
#include <unistd.h>
#endif

namespace ocr {

#ifdef _WIN32

namespace {

std::wstring widen(const std::string &text)
{
    int size = MultiByteToWideChar(CP_UTF8, 0, text.data(), int(text.size()),
                                   nullptr, 0);
    std::wstring wide(size, L'\0');
    MultiByteToWideChar(CP_UTF8, 0, text.data(), int(text.size()),
                        wide.data(), size);
    return wide;
}

// Quoted the way CommandLineToArgvW and the C runtime split it again
std::wstring quote(const std::wstring &arg)
{
    std::wstring out = L"\"";
    size_t backslashes = 0;
    for (wchar_t c : arg) {
        if (c == L'\\') {
            backslashes++;
            continue;
        }
        size_t repeat = c == L'"' ? 2 * backslashes + 1 : backslashes;
        out.append(repeat, L'\\');
        out += c;
        backslashes = 0;
    }
    out.append(2 * backslashes, L'\\');
    return out + L"\"";
}

// A job object kills its processes when its last handle closes, which
// also happens when this process is killed
HANDLE kill_on_close_job()
{
    HANDLE job = CreateJobObjectW(nullptr, nullptr);
    JOBOBJECT_EXTENDED_LIMIT_INFORMATION info = {};
    info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
    SetInformationJobObject(job, JobObjectExtendedLimitInformation, &info,
                            sizeof info);
    return job;
}

} // namespace

int run_program(const std::string &program,
                const std::vector<std::string> &args)
{
    std::wstring line = quote(widen(program));
    for (const std::string &arg : args)
        line += L" " + quote(widen(arg));

    HANDLE output = nullptr;
    DuplicateHandle(GetCurrentProcess(), GetStdHandle(STD_ERROR_HANDLE),
                    GetCurrentProcess(), &output, 0, TRUE,
                    DUPLICATE_SAME_ACCESS);
    STARTUPINFOW startup = {};
    startup.cb = sizeof startup;
    startup.dwFlags = STARTF_USESTDHANDLES;
    startup.hStdOutput = startup.hStdError = output;

    PROCESS_INFORMATION child = {};
    HANDLE job = kill_on_close_job();
    DWORD code = DWORD(-1);
    if (CreateProcessW(nullptr, line.data(), nullptr, nullptr, TRUE,
                       CREATE_NO_WINDOW | CREATE_SUSPENDED, nullptr, nullptr,
                       &startup, &child)) {
        AssignProcessToJobObject(job, child.hProcess);
        ResumeThread(child.hThread);
        WaitForSingleObject(child.hProcess, INFINITE);
        GetExitCodeProcess(child.hProcess, &code);
        CloseHandle(child.hThread);
        CloseHandle(child.hProcess);
    }
    CloseHandle(job);
    if (output)
        CloseHandle(output);
    return int(code);
}

std::string program_dir()
{
    wchar_t path[MAX_PATH * 4];
    DWORD size = GetModuleFileNameW(nullptr, path, DWORD(std::size(path)));
    std::wstring dir(path, size);
    dir = dir.substr(0, dir.find_last_of(L"\\/"));

    int bytes = WideCharToMultiByte(CP_UTF8, 0, dir.data(), int(dir.size()),
                                    nullptr, 0, nullptr, nullptr);
    std::string utf8(bytes, '\0');
    WideCharToMultiByte(CP_UTF8, 0, dir.data(), int(dir.size()), utf8.data(),
                        bytes, nullptr, nullptr);
    return utf8;
}

#else

int run_program(const std::string &program,
                const std::vector<std::string> &args)
{
    // Built before fork(): the child may only call async-signal-safe code
    std::vector<char *> argv{const_cast<char *>(program.c_str())};
    for (const std::string &arg : args)
        argv.push_back(const_cast<char *>(arg.c_str()));
    argv.push_back(nullptr);

    pid_t parent = getpid();
    pid_t pid = fork();
    if (pid == 0) {
        prctl(PR_SET_PDEATHSIG, SIGKILL);
        if (getppid() != parent)
            _exit(127);
        dup2(STDERR_FILENO, STDOUT_FILENO);
        execv(argv[0], argv.data());
        _exit(127);
    }
    if (pid < 0)
        return -1;

    int status = 0;
    while (waitpid(pid, &status, 0) < 0)
        if (errno != EINTR)
            return -1;
    return WIFEXITED(status) ? WEXITSTATUS(status) : -1;
}

std::string program_dir()
{
    char path[PATH_MAX];
    ssize_t size = readlink("/proc/self/exe", path, sizeof path);
    std::string exe(path, size > 0 ? size_t(size) : 0);
    return exe.substr(0, exe.find_last_of('/'));
}

#endif

} // namespace ocr
