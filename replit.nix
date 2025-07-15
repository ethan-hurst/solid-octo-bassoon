{ pkgs }: {
  deps = [
    pkgs.python312
    pkgs.python312Packages.pip
    pkgs.python312Packages.poetry-core
    pkgs.nodejs_20
    pkgs.postgresql_15
    pkgs.redis
    pkgs.git
    pkgs.bash
    pkgs.gnumake
  ];
  env = {
    PYTHON_LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
      pkgs.stdenv.cc.cc.lib
      pkgs.zlib
      pkgs.glib
      pkgs.xorg.libX11
      pkgs.xorg.libXext
      pkgs.xorg.libXinerama
      pkgs.xorg.libXcursor
      pkgs.xorg.libXrender
      pkgs.xorg.libXi
      pkgs.xorg.libXfixes
      pkgs.pango
      pkgs.cairo
      pkgs.freetype
      pkgs.fontconfig
      pkgs.gtk3
      pkgs.graphite2
      pkgs.harfbuzz
      pkgs.atk
      pkgs.gdk-pixbuf
      pkgs.cairo
      pkgs.glib
      pkgs.harfbuzz
    ];
    PYTHONBIN = "${pkgs.python312}/bin/python3.12";
    LANG = "en_US.UTF-8";
    LC_ALL = "en_US.UTF-8";
  };
}