(From Gabriel Rodrigues to Gabriel Rodrigues file)

# Releasing updates to the Launchpad PPA (pr-ship)

This is a practical, repeatable checklist to publish a new version to Launchpad PPA.

# 0) Identity (ok to keep)
export DEBEMAIL="gabrielrod.ifmg@gmail.com"
export DEBFULLNAME="Gabriel Rodrigues"

# 1) Create the orig tarball for <VERSION> (IMPORTANT)
tar --exclude-vcs --exclude='./debian' -czf ../pr-ship_<VERSION>.orig.tar.gz .

# 2) Build signed source package, including orig tarball
debuild -S -sa

# 3) Upload
dput ppa:gabsdk/pr-ship ../pr-ship_<VERSION>-1~ppa2~ubuntu24.04.1_source.changes