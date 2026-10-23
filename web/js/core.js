// What the desktop and Android engines share: the options of
// "ocr-pdf-core run" and the meaning of the lines it writes
// (core/src/cli.cpp)

// App.options() as arguments
export function runOptions(options) {
    const args = ['--languages', options.languages.join('+')];
    if (options.force) args.push('--force');
    if (options.deskew) args.push('--deskew');
    return args;
}

// A line on stdout is a JSON message; anything else goes to the log
export function coreMessage(line, stream) {
    if (stream === 'stdout') {
        try {
            return JSON.parse(line);
        } catch {
            // not a message: logged below
        }
    }
    return { event: 'log', level: stream, msg: line };
}
