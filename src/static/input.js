// Drag and drop: put the dropped file into the file input, and pick SDD/SDR from its content when it is obvious.
const drop = document.getElementById('drop');
const fileInput = document.getElementById('file');

drop.addEventListener('dragover', (event) => { event.preventDefault(); drop.classList.add('over'); });
drop.addEventListener('dragleave', () => drop.classList.remove('over'));
drop.addEventListener('drop', (event) => {
  event.preventDefault();
  drop.classList.remove('over');
  if (event.dataTransfer.files.length) {
    fileInput.files = event.dataTransfer.files;
    guessType(event.dataTransfer.files[0]);
  }
});
fileInput.addEventListener('change', () => { if (fileInput.files.length) guessType(fileInput.files[0]); });
document.getElementById('text').addEventListener('input', (event) => guessFromText(event.target.value.slice(0, 4000)));

function guessType(file) { file.slice(0, 4000).text().then(guessFromText); }

// SDR files have "***subheader" cell blocks; anything else with text is assumed to be SDD. The user can still change it.
function guessFromText(text) {
  if (!text.trim()) return;
  const type = /\*\*\*\s*subheader/i.test(text) ? 'sdr' : 'sdd';
  document.querySelector(`input[name=input_file_type][value=${type}]`).checked = true;
}

// htmx ignores answers with an error status (for example 500 or 502), so without this the page would show nothing
// at all when the server fails. Show a short message in the result box instead.
function showServerError(text) {
  document.getElementById('result').innerHTML =
    '<article><header class="error"><strong>Could not draw the karyograms</strong></header><p>' + text + '</p></article>';
}
document.body.addEventListener('htmx:responseError', (event) =>
  showServerError('The server had a problem (error ' + event.detail.xhr.status + '). Please try again later, ' +
                  'or tell the site maintainer if it keeps happening.'));
document.body.addEventListener('htmx:sendError', () =>
  showServerError('Could not reach the server. Check your internet connection and try again.'));
