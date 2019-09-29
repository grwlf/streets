#{ pkgs ?  import ./lib/nixpkgs {}
{ pkgs ?  import <nixpkgs> {}
, stdenv ? pkgs.stdenv
} :
let

  self = pkgs.python37Packages;
  inherit (pkgs) fetchgit;
  inherit (self) buildPythonPackage fetchPypi;

  jsonpickle = buildPythonPackage rec {
    name = "jsonpickle-${version}";
    version = "0.9.5";

    buildInputs = with self; [ numpy ];

    src = pkgs.fetchurl {
      url = "https://github.com/jsonpickle/jsonpickle/archive/v${version}.tar.gz";
      sha256 = "1x79vlyzcva9g4g4xs59ipjgqfrsm7kkglsqqkgkqv9fa299s2bj";
    };
  };

  virtual-display = buildPythonPackage rec {
    name = "PyVirtualDisplay-0.1.5";

    propagatedBuildInputs = with self; [ EasyProcess ];
    doCheck = false;

    src = pkgs.fetchurl {
      url = "mirror://pypi/P/PyVirtualDisplay/${name}.tar.gz";
      sha256 = "aa6aef08995e14c20cc670d933bfa6e70d736d0b555af309b2e989e2faa9ee53";
    };
  };


  pyls = self.python-language-server.override { providers=["pycodestyle" "pyflakes"]; };
  pyls-mypy = self.pyls-mypy.override { python-language-server=pyls; };

  be = stdenv.mkDerivation {
    name = "buildenv";
    buildInputs =
    ( with pkgs;
      with self;
    [
      sqliteman
      ipython
      sqlite


      # The next tools are compatible with the
      # `LanguageClient-neovim` VIM plugin
      pyls-mypy
      pyls
      # pyls-isort
      # pyls-black

      # Selenium-related stuff
      pyyaml
      virtual-display
      xorg.xorgserver
      selenium
      chromedriver
      chromium

    ]);

    shellHook = with pkgs; ''
      if test -f ./env.sh ; then
        . ./env.sh
      fi
    '';
  };

in
  be
