// Updates of the apps from the repository's GitHub releases. The page asks
// GitHub for the latest release and picks its file for this app; the app
// downloads and installs it (desktop/src/update.rs).

import { LATEST_RELEASE_API, UPDATE_FILES } from './config.js';

// v<x.y.z>, as the tags and APP_VERSION (mk/version.mk) begin
const VERSION = /^v(\d+)\.(\d+)\.(\d+)/;

export function parseVersion(text) {
    const match = VERSION.exec(text ?? '');
    return match ? match.slice(1).map(Number) : null;
}

export function isNewer(version, than) {
    const differs = version.findIndex((part, i) => part !== than[i]);
    return differs >= 0 && version[differs] > than[differs];
}

// release: GitHub's answer; current: APP_VERSION; kind: a key of
// UPDATE_FILES, or null when the app cannot install updates itself.
// Returns null, or the update: {from, to, page, file: {name, size} | null}.
export function findUpdate(release, current, kind) {
    const have = parseVersion(current);
    const latest = parseVersion(release?.tag_name);
    if (!have || !latest || !isNewer(latest, have)) return null;

    const suffix = UPDATE_FILES[kind];
    const asset = suffix && (release.assets ?? []).find(
        (file) => file.name.endsWith(suffix));
    return {
        from: current.split('+')[0],
        to: release.tag_name,
        page: release.html_url,
        file: asset ? { name: asset.name, size: asset.size } : null,
    };
}

// Throws when GitHub cannot be reached
export async function checkForUpdate(current, kind) {
    if (!parseVersion(current)) return null;
    const response = await fetch(LATEST_RELEASE_API,
        { headers: { Accept: 'application/vnd.github+json' } });
    if (!response.ok) return null;
    return findUpdate(await response.json(), current, kind);
}

// The commands of desktop/src/update.rs, the same in both apps
export const appUpdates = {
    kind: () => window.__TAURI__.core.invoke('update_package'),

    install(update, onPercent) {
        const { invoke, Channel } = window.__TAURI__.core;
        const channel = new Channel();
        channel.onmessage = onPercent;
        return invoke('install_update', {
            tag: update.to,
            name: update.file.name,
            size: update.file.size,
            onPercent: channel,
        });
    },
};
