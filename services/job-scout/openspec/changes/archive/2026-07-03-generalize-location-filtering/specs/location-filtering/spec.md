## MODIFIED Requirements

### Requirement: Non-Hungary country-specific roles are skipped
The filter SHALL return SKIP for any role whose job description names a specific single country other than Hungary as the required location, residency, work authorization, or physical presence — regardless of whether the role is otherwise remote, on-site, or hybrid.

This includes (but is not limited to):
- Explicit restriction phrasing: "for those based in the UK", "must be based in Germany", "must be a UK resident", "right to work in Ireland required" (without EU/international sponsorship mention)
- A bare single-country remote location label with no further restriction language: "Remote, UK", "Remote, Germany", "Remote, US"
- A requirement of physical on-site or hybrid presence in that country: "on-site in Berlin required", "hybrid, San Francisco office"
- A list of eligible countries that omits Hungary: "open to candidates based in Germany, Poland, or the Netherlands"

This requirement does NOT apply when Hungary is mentioned (alone or as one of several eligible countries) or when the role specifies a multi-region remote scope covered by the "Multi-region remote roles including EU are treated as relevant on location" requirement.

#### Scenario: JD opens with a country-specific restriction phrase
- **WHEN** the job description contains "for those based in the UK", "must be based in Germany", or an equivalent single-country restriction
- **THEN** the filter SHALL return SKIP

#### Scenario: JD lists a bare single-country remote label
- **WHEN** the job description lists location as "Remote, UK", "Remote, Germany", or a similar bare single-country label with no further restriction language
- **THEN** the filter SHALL return SKIP

#### Scenario: JD requires on-site or hybrid presence in a non-Hungary country
- **WHEN** the job description requires physical presence in a specific country other than Hungary (e.g. "on-site in Berlin required", "hybrid, San Francisco office"), whether or not that country is in the EU
- **THEN** the filter SHALL return SKIP

#### Scenario: JD lists eligible countries omitting Hungary
- **WHEN** the job description lists specific eligible countries (e.g. "open to candidates based in Germany, Poland, or the Netherlands") and Hungary is not among them
- **THEN** the filter SHALL return SKIP

#### Scenario: JD mentions Hungary as an eligible location
- **WHEN** the job description names Hungary as the required location, or as one of several eligible countries
- **THEN** location SHALL NOT be a basis for SKIP; verdict is determined by role fit

## REMOVED Requirements

### Requirement: UK-only remote roles are skipped
**Reason**: Superseded by "Non-Hungary country-specific roles are skipped", which generalizes this rule to any country other than Hungary instead of special-casing the UK.
**Migration**: No action needed — the UK is now covered as one instance of the general rule. The previous "Remote, UK with no restriction language → UNSURE" carve-out is retired; that case now returns SKIP under the new requirement.

### Requirement: Candidate location and relocation preference are encoded in filtering rules
**Reason**: Superseded by "Non-Hungary country-specific roles are skipped", which extends physical-presence SKIP scope from "outside Hungary/EU" to "outside Hungary" and folds the on-site/hybrid case into the same general rule as remote-with-country-label roles.
**Migration**: No action needed — on-site/hybrid roles requiring presence in a non-Hungary country (EU or not) are now covered by the new requirement.
