document.getElementById('enableBtn').addEventListener('click', () => {
  chrome.tabs.query({active: true, currentWindow: true}, tabs => {
    chrome.tabs.sendMessage(tabs[0].id, {action: "enableUploader"}, response => {
      if(response && response.status === "enabled"){
        document.getElementById('enableBtn').innerText = "Uploader Enabled";
        document.getElementById('enableBtn').disabled = true;
      }
    });
  });
});