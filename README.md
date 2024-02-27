<!--
MIT License

Copyright (c) 2021 Othneil Drew

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

-->

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/rplab/LS_Pycro_App">
    <img src="https://raw.githubusercontent.com/rplab/LS_Pycro_App/master/app_icon.png" alt="Logo" width="80" height="80">
  </a>

## rplab_image_analysis

  <p align="left">
    rplab_image_analysis is an image analysis library created by the Parthasarathy Lab in the Department of Physics at the University of Oregon.
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li>
      <a href="#usage">Usage</a>
      <ul>
        <li><a href="#bacterial_clusters">bacterial_clusters</a></li>
        <li><a href="#eukaryotic_cells">eukaryotic_cells</a></li>
        <li><a href="#general">general</a></li>
        <li><a href="#gui">gui</a></li>
        <li><a href="#gut_segmentation">gut_segmentation</a></li>
        <li><a href="#individual_bacteria">individual_bacteria</a></li>
        <li><a href="#tests">tests</a></li>
        <li><a href="#utils">utils</a></li>
        <li><a href="#visualization">visualization</a></li>
      </ul>
    </li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>



<!-- GETTING STARTED -->
## Getting Started

### Prerequisites

This program requires Python 3.9 or later.

### Installation

1. Clone the repo
   ```sh
   git clone https://github.com/rplab/LS_Pycro_App
   ```
2. pip install
   ```sh
   pip install /local/repo/path
   ```



## Usage
This project is split into several modules, split by analysis topic. Each one is designed to be used as a python package with API functions and classes.

### bacterial_clusters
Not yet implemented

### eukaryotic_cells
Not yet implemented

### general
The general package contains tools for image processing. It currently contains the following modules:

  <li>background_subtraction</li>
  <li>combined_process</li>
  <li>downsampling</li>
  <li>max_projections</li>
  <li>png_conversion</li>
  <li>stitching</li>
</ul>


### gui
Not yet implemented

### gut_segmentation
Not yet implemented

### individual_bacteria
Not yet implemented

### tests
The test package includes tests for functions used throughout the other packages.

### utils
The utils package contains functions and classes used by the other analysis packages. This includes objects like
filepath manipulation, loading in images, and metadata extraction.

### visualization
Not yet implemented



<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

Email: rpbiolab@gmail.com

Project Link: [https://github.com/rplab/rplab_image_analysis](https://github.com/rplab/rplab_image_analysis)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* [scikit-image]()
* [tifffile](https://github.com/cgohlke/tifffile)
* [micro-manager](https://github.com/micro-manager/micro-manager)

<p align="right">(<a href="#readme-top">back to top</a>)</p>
