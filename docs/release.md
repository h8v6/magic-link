# Release Process

1. Ensure `main` is green (CI passing, documentation up to date).
2. Update `CHANGELOG.md` with the release date and highlights.
3. Bump the version in `pyproject.toml` if needed.
4. Commit the release prep (`git commit -am "chore: prepare release vX.Y.Z"`).
5. Tag the commit: `git tag vX.Y.Z && git push origin vX.Y.Z`.
6. Draft a GitHub Release using the changelog entry.
7. Once the release is published, the `Publish` workflow builds and uploads the distribution to PyPI using `PYPI_API_TOKEN`.
8. Announce the release and update documentation links if applicable.

For test uploads, create a pre-release tag and use TestPyPI by temporarily adjusting the workflow or running `python -m build && twine upload` locally.
