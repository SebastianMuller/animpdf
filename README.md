# animpdf

This is a command line program / Python script that modifies PDF files in a way helpful for presentations. It generates a new PDF file where the text appears line by line (as with the \pause command in LaTeX). It also displays the previous slide next to the current one so that it is possible to refer back. These features help to emulate the didactical advantages of a chalkboard, even for handwritten presentations. Either of them can be switched off if desired.




## "Installation"

Download using 'Clone or download' above. The executables files for Linux, MacOS or Windows can be found in the corresponding directory. They can be used directly.

Alternatively, use the Python script from above. 

In both cases, Ghostscript needs to be installed on your system. Ghostscript is available from https://www.ghostscript.com/download/gsdnld.html for Windows and Linux. Instructions for MacOS can be found on http://macappstore.org/ghostscript/.



## How to use

Prepare a PDF file including the slides. For example this can be generated by LaTeX or Powerpoint, handwritten on a tablet, or written on paper and scanned in.

When preparing the slides, note that animpdf believes that elements of text separated by continuous horizontal white lines are intended to be displayed as subsequent lines in the presentation. Hence slightly diagonal writing will not work. Pictures displayed on the side next to a couple of lines of text cause these lines to be merged, hence it is preferable to place pictures vertically between text. Sometimes i-dots or integration limits are treated as a line on their own but I did not find this much of a problem.

Open a terminal window, go to the directory containing the executable file and run the program using

```
  animpdf filename
```

where filename is the name of the input file excluding '.pdf' (plus path if it's not in the same directory). The output then appears in the file filename_anim.pdf.

Optional parameters are:

```
  --rotate ROTATE       rotate input by the angle ROTATE
  --nohistory           do not display previous slide
  --nolines             do not animate line by line
  --flatten             use this if PDF annotations are missing from the output
  --place PLACE         placement of previous slide: left(default), right, top, bottom
  --addname ADDNAME     change addition to output file name (default: '_slides')
  -h, --help            show the help message and exit
```

The option ```--rotate``` can be helpful if a landscape slide is scanned as if it were in portrait format, and the option ```--flatten``` should be used if the output looks incomplete.

If using Python directly one can also modify the final line of the script, and pass the filename and optional parameters to the ```anim_pdf``` command.

There are a number of programs that can be used to edit files before using animpdf, for example to cut or merge PDF files. A free option is PDFsam Basic https://pdfsam.org/.

