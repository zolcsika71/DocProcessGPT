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

{
  environment.systemPackages = with pkgs; [
    glibcLocales
  ];

  environment.variables = {
    LANG = "en_AU.UTF-8";
    LC_ALL = "en_AU.UTF-8";
  };
}

