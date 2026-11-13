# Local GPS navigation preview

This change is local only. It does not change the deployed Netlify site.

## Try it

1. Open `http://127.0.0.1:8787/app.html?mode=route&example=1`.
2. Choose **Preview walk** to simulate movement along the selected least-friction route. No location permission is requested. The simulation is labeled and runs at 12 times the assumed walking speed; use the slider to inspect another part of the route.
3. Choose **Start route** for browser GPS guidance. Location is requested only after this click. Guidance shows the next geometrically inferred turn, approximate remaining distance/time, and GPS accuracy.
4. Use **Stop** to end tracking. Leaving the tab pauses tracking; returning requires **Resume**.

## What this does

- Uses the exact edge sequence of the selected least-friction route, not the time-only alternative.
- Orients edge geometries to their graph direction and does not invent connections across geometry gaps.
- Projects fresh, sufficiently accurate GPS positions onto the route. Continuity checks reduce jumps to nearby later sections.
- Shows off-route, low-accuracy, stale-signal and mapped-gap messages without automatically switching objectives or rerouting.
- Announces a mapped route end only after two sufficiently accurate fixes, at least half a second apart, near the end. This is not confirmation of the building entrance.
- Offers optional spoken cues. No Google Directions or additional paid API is used.
- Keeps GPS fixes in the open page's memory; no application GPS-history upload, analytics event or persistent GPS storage is added. Basemap tiles are still fetched for the viewed map extent.

## Limits and field evaluation

This is foreground browser guidance, not a Google Maps-equivalent or independently validated navigation system. The OSM graph may contain road centerlines instead of exact sidewalks. Private driveways, verified entrances, crossing signals, closures, curb ramps and accessibility barriers are not established by the route geometry. Residential addresses currently map to block reference nodes.

Turn cues come from path geometry, not validated pedestrian maneuvers or live crossing conditions. GPS alone cannot reliably distinguish every pair of parallel sidewalks. Keep the screen/tab active; mobile background tracking and offline routing are not provided. The browser attempts a screen wake lock when available; this is not guaranteed.

A phone cannot reach a laptop by opening `127.0.0.1`. Later phone testing needs a separately authorized HTTPS preview or a secure development connection. No public tunnel or deployment is created by this change.

Before public release, audit representative routes on foot and with aerial/street imagery; test turns, parallel paths, crossings, signal loss, battery use, route joins and destination approaches across Android/iOS. Compare actual GPS traces with surveyed pedestrian paths and report positional and maneuver errors. Simulated tests do not establish outdoor accuracy or safety.

## Verification

- `node tests/test_navigation_core.cjs`
- `PLAYWRIGHT_MODULE=/path/to/playwright node tests/test_navigation_browser.cjs`

The browser tests use mocked GPS in an isolated browser context. They check that preview requests no GPS, live progress uses the selected route, weak fixes do not advance progress, off-route recovery works, permission errors are handled, leaving the tab pauses tracking, stopping clears location watches, and the mobile map exposes navigation controls.

Browser API references: [Geolocation watchPosition](https://developer.mozilla.org/en-US/docs/Web/API/Geolocation/watchPosition), [clearWatch](https://developer.mozilla.org/en-US/docs/Web/API/Geolocation/clearWatch), [Page Visibility](https://developer.mozilla.org/en-US/docs/Web/API/Page_Visibility_API).
