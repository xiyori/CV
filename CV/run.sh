#!/bin/bash

cd CV
pdflatex -interaction=nonstopmode main.tex
rm main.aux main.out main.log
