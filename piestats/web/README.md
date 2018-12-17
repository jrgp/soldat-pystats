# Pystats Frontend README

The Pystats UI is a SPA (single-page-app) composed a backend and a frontend:

- Backend is a Python REST API (returns json) powered by falcon/gevent
- Frontend powered by React/React-router

To enable ease of use for the app, we commit the built bundles to git, so the commands
needed here are only useful if you want to edit and rebuild the react frontend.

#### Useful paths

- `piestats/web/react_app/` - React JSX frontend source files
- `piestats/web/static/` - Corresponds to `/static/` URL route for static assets
- `piestats/web/static/webpack/` - Where our compiled JSX goes. Commit to git.
- `piestats/web/templates/` - Server-rendered jinja2 templates, just for root SPA file
- `piestats/web/app.py` - Python Falcon REST-api code
- `piestats/web/results.py` - Interacts with Redis and the rest of the pystats code. Used by `app.py`.

#### React dev quickstart

Run these commands in the `piestats/web/` folder.

Install deps needed for building:

    npm install

Buld in development mode, so browser console is useful

	npm run dev

Build in release/production mode, for committing to git and serving

	npm run build