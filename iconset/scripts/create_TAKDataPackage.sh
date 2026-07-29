#!/bin/bash
cd source
zip -r "../datapackage/iconsets/SafeSwim NZ.zip" iconset.xml Safeswim/
cd ../datapackage
zip -r "../SafeSwimNZ-Package.zip" MANIFEST/ iconsets/
