# Contributing

## Workflow

1. Start from an up-to-date `main` branch and create a focused feature or
   milestone branch.
2. Open or reference a GitHub issue with testable acceptance criteria.
3. Keep commits small, meaningful, and written in imperative Conventional
   Commit style where practical.
4. Run focused checks while developing and the full verification suite at a
   milestone boundary.
5. Open a draft pull request with the problem, implementation, GIS methodology
   where relevant, validation, limitations, and linked issues.
6. Do not merge without the repository owner's explicit approval.

## Development standards

- Do not commit secrets, downloaded source data, or generated spatial outputs.
- Record source provenance and licensing before adding a dataset to the
  pipeline.
- Add or update tests with behavior changes.
- Keep proprietary ArcGIS workflows optional so the open-source core remains
  reproducible.
- Never describe Euclidean buffers as walking routes or report findings that
  have not been computed and validated.

Run the commands in the README's **Verification** section before requesting
review.
