# SOUP Register

SOUP means software of unknown provenance used by the product but not developed
under this repository's software lifecycle controls.

The release React licensing UI does not currently vendor third-party browser
libraries directly into the repository source. Frontend dependencies are managed
through `apps/ui/package.json` and should be reviewed through the normal package
dependency and security scan process.

If a browser library is vendored again for offline use, add a new entry here
with version, source artifact, license, hash, intended use, failure modes,
verification, and maintenance policy.
