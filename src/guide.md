<!--
  This file is the "How to use" section at the top of the website's page.
  Write it like a README: ### for headings (the section itself is the big heading), - for lists, **bold**, [link text](https://...).
  Lines between these comment markers are not shown on the page.
  After editing: commit, push, git pull on the VPS. The page changes at once; the "Last updated" date
  changes after: sudo systemctl restart karyoke-web
  To add a picture: put the PNG in static/ (for example static/guide-viewer.png) and write
  ![Karyogram viewer](/guide-viewer.png)
-->

KaryoKE draws one karyogram per cell from Standard for DNA Damage (SDD) or Standard for DNA Repair (SDR)
data, so you can see at a glance which chromosomes are damaged or mutated.

### Quick start

1. Choose the **file type** and the **genome**.
2. Drop your file onto the dashed box, click **Choose File**, or paste the file's contents into the text box.
3. Click **Draw karyograms**.
4. When "Karyograms ready" appears, click **Open karyogram viewer** or **Download summary file**.

### The input section

- **File type**
  - **SDR (mutations)**: an SDR file, with the mutations left after DNA repair<sup><a id="cite-1" href="#ref-1">[1]</a></sup>.
  - **SDD (DNA damage)**: an SDD file, with the DNA damage before repair<sup><a id="cite-2" href="#ref-2">[2]</a></sup>.
  - When you drop or choose a file, the page picks the file type for you if the file makes it obvious.
    Check it before you click Draw karyograms.
- **Genome**
  - **Human**: chromosomes are drawn with realistic human centromere positions.
  - **Other**: generic centromere positions, for any other genome.
- **Data**: a file or pasted text. If you do both, the file is used and the text box is ignored.
- **Draw karyograms**: sends the data to the server and runs KaryoKE<sup><a id="cite-3" href="#ref-3">[3]</a></sup>. Large files can take a minute or two.

### The results

- **Open karyogram viewer**: opens the karyograms in a new tab.
- **Download summary file**: a text file with, for each cell, the number of each kind of mutation (SDR)
  or damage (SDD), in total and by chromosome.

### The karyogram viewer

<!-- TODO: describe these in your own words, and add a screenshot -->

- Switching between cells:
- Zooming in and out:
- Clicking a chromosome: shows the damage or mutations on each homolog of that chromosome.
- Downloads: each karyogram as PNG or SVG, or all of them at once as a .zip file.

<!-- TODO: legend: colours, symbols, what each kind of mutation or damage looks like -->

### Limits and privacy

- Files can be up to 50 MB. For bigger files, use the KaryoKE program on your own computer<sup><a id="cite-3" href="#ref-3">[3]</a></sup>.
- A run that takes longer than 5 minutes is stopped.
- Your data and results are kept on the server only to show them to you, and are deleted after 60 minutes.

### Common problems

- **"KaryoKE could not process this data"**: check that the file type matches the file (SDR or SDD).
  The messages under the error come from KaryoKE and say what it could not read.
- **"The server is busy"**: other people are drawing karyograms. Try again in a minute.
- **"Results no longer available"**: results are deleted after 60 minutes. Run your data again.

### Citations

[1] <span id="ref-1"></span>https://github.com/Zhenlun/generate-standard-DNA-repair-with-medras-mc

[2] <span id="ref-2"></span>Schuemann, J., McNamara, A. L., Warmenhoven, J. W., Henthorn, N. T., Kirkby, K. J., Merchant, M. J., Ingram, S., Paganetti, H., Held, K. D., Ramos-Mendez, J., Faddegon, B., Perl, J., Goodhead, D. T., Plante, I., Rabus, H., Nettelbeck, H., Friedland, W., Kundrát, P., Ottolenghi, A., Baiocco, G., … McMahon, S. J. (2019). A New Standard DNA Damage (SDD) Data Format. Radiation research, 191(1), 76–92. https://doi.org/10.1667/RR15209.1

[3] <span id="ref-3"></span>https://github.com/kildealab/KaryoKE

<!-- TODO: paper or software citation, once there is one -->

Questions or problems: open an issue on [GitHub](https://github.com/kildealab/KaryoKE)
or contact the [Kildea Lab](https://kildealab.com).
