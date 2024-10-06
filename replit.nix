{pkgs}: {
  deps = [
    pkgs.glibcLocales
    pkgs.freetype
    pkgs.openssl
    pkgs.postgresql
    pkgs.bashInteractive
    pkgs.glibcLocales
    pkgs.python311
    pkgs.nodePackages.pyright
    pkgs.poetry
  ];
}

