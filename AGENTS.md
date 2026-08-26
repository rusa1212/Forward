# forward

React + Vite + Tailwind CSS project, structured as an npm workspace.

## Development Server

Run `npm run dev` from the repo root (delegates to `front`) to start the Vite dev server on `$PORT` (default 8443).

- Hot reload: Changes to source files are reflected immediately

## Project Structure

This repo is an npm workspace with a single package, `front`. This is the canonical project structure. Start with task-relevant files below. Only follow imports or inspect other files when required, when a documented path is missing, or when the repository contradicts this guide.

- `front/src/main.tsx` - React entrypoint; imports `front/src/index.css` and mounts `front/src/App.tsx` into the `#root` element
- `front/src/App.tsx` - Primary application component and the usual starting point for UI work
- `front/src/index.css` - Global CSS entrypoint and Tailwind CSS v4 import
- `front/index.html` - Vite HTML shell containing the `#root` element and loading `front/src/main.tsx`
- `front/package.json` - Frontend package (`forward-frontend`) with dependencies and the Vite build, development, preview, and formatting scripts
- `front/vite.config.ts` - Vite configuration with React, Tailwind CSS v4, and the `@` alias for `front/src`
- `package.json` - Workspace root; declares the `front` workspace and delegates `dev`/`build`/`preview`/`format` to it via `npm run <script> --workspace=front`
- `.mise.toml` - Toolchain version for Node.js

## Dependencies

- Runtime: React 19 and React DOM 19
- Styling: Tailwind CSS v4 with the `@tailwindcss/vite` plugin
- Build tooling: Vite 8, TypeScript 5.7, and `@vitejs/plugin-react`
- Formatting: oxfmt

## Styling

This project uses **Tailwind CSS v4** through the `@tailwindcss/vite` plugin configured in `front/vite.config.ts`. `front/src/index.css` imports Tailwind with `@import 'tailwindcss';`. Use Tailwind utility classes directly in JSX and put global CSS or Tailwind v4 theme customization in `front/src/index.css`. This scaffold does not need a Tailwind config file or PostCSS config.

`front/src/main.tsx` imports `front/src/index.css`, so global font wiring belongs in `front/src/index.css`. Keep CSS `@import` statements first, then add any `@font-face` rules and font-family defaults there.

## Code quality

- Use double quotes for strings containing apostrophes (`"We're here to help"`), or escape them in single-quoted strings. An unescaped apostrophe in a single-quoted string breaks the build.
- Ensure JSX tags are closed and braces are balanced.
- Export components as default exports.
