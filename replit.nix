{pkgs}: {
  deps = [
    pkgs.glibcLocales
    pkgs.freetype
    pkgs.openssl
    pkgs.postgresql
    pkgs.bashInteractive
    pkgs.glibcLocales
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

