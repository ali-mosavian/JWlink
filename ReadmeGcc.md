jwlink Compilation:

cd dwarf/dw
make -f GccUnix.mak
cd ../../orl
make -f GccUnix.mak
cd ../sdk/rc/wres
make -f GccUnix.mak
cd ../../..
make -f GccUnix.mak
Tests (need python3; pass the jwlink to test, default GccUnixR/jwlink):

python3 tests/run_tests.py
