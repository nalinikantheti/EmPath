# Share EmPath maps

## Easiest immediate method: share the ZIP
Upload `output/team_share/EmPath_maps.zip` to Google Drive and give teammates access. They download and unzip it, then open `index.html`. Keep the folder together. This is a local interactive viewer, not a publicly hosted website. Internet access is needed for basemap tiles and JavaScript libraries.

## Google Sites
Google Sites supports Insert > Embed > By URL, or Embed code. For these large interactive maps, host the map folder first and embed its HTTPS URL. Google Drive file sharing is a download option, not a static HTML web host.

After hosting, replace `YOUR_HOSTED_MAP_URL` below with the map's actual HTTPS address:

```html
<iframe src="YOUR_HOSTED_MAP_URL" title="EmPath interactive map"
        width="100%" height="750" style="border:0"
        loading="lazy" allowfullscreen></iframe>
```

Do not paste local `file:///` paths or `localhost` URLs into Google Sites: teammates cannot access your computer through them. Do not treat an example domain as a real published URL.

## Google Docs
Insert a map PNG, then add descriptive text and use Insert > Link (Cmd+K). Use a shared Drive ZIP link for downloads or the hosted map URL for live interaction. Google Docs cannot run the map inline.

## Hosting choices
A static host such as GitHub Pages or a drag-and-drop static hosting service can serve the folder. No public deployment has been performed. The generated maps contain the browser-visible CARTO basemap key; configure it for the intended public domain and provider permissions before public deployment. The sharing ZIP deliberately excludes `.env` and other project data.

References: https://support.google.com/sites/answer/90569 and https://support.google.com/docs/answer/45893
