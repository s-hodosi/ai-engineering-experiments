# Spec: Dark Theme

## Purpose

Defines requirements for the warm dark color palette applied across all UI elements.

## Requirements

### Requirement: Warm dark color palette applied to all UI elements
The UI SHALL use a warm dark color palette defined via CSS custom properties. All backgrounds, surfaces, text, borders, inputs, buttons, and result cards SHALL use the defined palette. No element SHALL retain the previous light theme colors.

#### Scenario: Body background is dark warm brown
- **WHEN** the page loads
- **THEN** the body background is `#1a1714` and primary text is `#ede8e0`

#### Scenario: Cards use dark warm charcoal surface
- **WHEN** result cards are rendered
- **THEN** each card background is `#242220` with a subtle border of `#3a3530`

#### Scenario: Inputs are styled for dark theme
- **WHEN** the user focuses a textarea
- **THEN** the textarea has background `#2e2b28`, text `#ede8e0`, and a visible focus border using the accent color `#60a5fa`

#### Scenario: Button uses accessible contrast on dark background
- **WHEN** the Analyze button is visible
- **THEN** it uses accent color `#60a5fa` as background with dark text, maintaining a contrast ratio of at least 4.5:1

### Requirement: Color palette defined via CSS custom properties
The palette SHALL be defined once on `:root` using CSS custom properties so all colors are maintainable from a single location.

#### Scenario: CSS variables defined on root
- **WHEN** the page CSS is parsed
- **THEN** `:root` defines at minimum `--bg`, `--surface`, `--surface-2`, `--border`, `--text`, `--muted`, `--accent`, and `--success`
