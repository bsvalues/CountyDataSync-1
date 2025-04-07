{pkgs}: {
  deps = [
    pkgs.geos
    pkgs.unixODBC
    pkgs.glibcLocales
    pkgs.postgresql
    pkgs.openssl
  ];
}
