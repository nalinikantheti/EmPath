# Methodology page and community feedback

`netlify_site/src/method.html` is the maintained methodology page. The build also publishes the same content at `behind.html` so existing links, including `#coverage`, continue to work. For source-only previews, `behind.html` redirects to `method.html`.

The page uses the research proposal, algorithm guide and roadmap, checked against the current implementation JSON under `src/data/`. Personal background from the proposal is not published. The four GeoAI sequence figures and their keyboard-accessible tabs now live on Methodology rather than the gallery. The captions retain the original 5 m corridor measurements and explain the current 20 m-wide corridor.

The three interactive examples are educational: segment-cost sliders use the current stated-preference formula; the Dijkstra illustration compares accumulated route costs; the category table demonstrates averages, missing routes and changing winners. They do not modify production analysis data.

## Feedback data

The initial three genuine anonymous comments were imported from Netlify notification emails in the owner's connected Gmail account on November 14, 2026. An automated setup-test submission was excluded. `src/data/public-feedback.json` contains only comment text, public IDs and submission times—no email headers, account details or notification links.

The public board uses Netlify Blobs through `/.netlify/functions/feedback`. Deploy with the normal Netlify build (`npm ci` in `netlify_site`, then `node ../scripts/build_netlify_site.mjs`). Netlify supplies the site storage context; no Gmail connection or API token is used by the website. Deploy the functions and dependencies as well as static assets. A static-only upload cannot enable shared voting.

Votes are immutable records keyed by idea and a signed random browser identifier. Conditional writes and strong consistency prevent concurrent duplicate clicks or lost increments. The signing key lives in the private blob store. HTTP-only, Secure, SameSite cookies remember votes. POSTs require a matching Origin. This is informal browser-based voting, not authenticated one-person-one-vote: clearing cookies or changing browsers allows another vote. No IP address is stored by this feature.

The Netlify `submission-created` event adds new verified form submissions when `share-publicly=yes`. The form submits this field automatically: ideas are anonymous and public by default. Legacy submissions without that field remain private. The UI uses text nodes rather than interpreting comments as HTML. Sorting is descending helpful votes, then newest submission, then stable ID. There is no automated email inbox scraping.

To remove a public idea, remove an imported seed entry or its `ideas/<id>` blob as applicable. For abusive new submissions, also mark the form submission as spam in Netlify. The board is an anonymous research feedback feature; it does not provide account-based moderation or identity verification.

When the live API is unavailable, the page shows the three imported comments and explicitly disables voting. Zeroes in this fallback are not presented as current shared counts. Local static previews do not send submissions.

## Validation

```
node --test tests/feedback.test.mjs
node --check netlify_site/src/methodology.js
node --check netlify_site/src/feedback.js
node scripts/build_netlify_site.mjs
```

Backend tests exercise concurrent/repeated voting, multiple browsers, invalid requests, sorting, private submissions and replayed events. Browser review covers ZIP-image tabs, slider arithmetic, route-search stages, category changes, unreachable destinations, no-category state, feedback reordering after a vote and page reload, and narrow-screen layout. Production storage and event delivery must also be smoke-tested after deploying; local tests do not contact the live Netlify store or submit test feedback to the owner's inbox.
