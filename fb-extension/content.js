(function(){
  console.log("Messenger Image Uploader content script loaded in off state.");

  let observerActive = false;
  let observer = null;

  // Helper function to fetch the image and send it to localhost.
  async function uploadImage(imgSrc) {
    try {
      const imageResponse = await fetch(imgSrc);
      const imageBlob = await imageResponse.blob();
      const formData = new FormData();
      formData.append('file', imageBlob, 'messenger-image.jpg');

      const res = await fetch("http://localhost:8000/upload-image/", {
        method: "POST",
        body: formData,
      });
      
      const data = await res.json();
      console.log("Image uploaded:", data);
    } catch (error) {
      console.error("Error uploading image:", error);
    }
  }

  // Process a message row. If it contains an image message, upload it.
  function processImageMessage(row) {
    const imageLink = row.querySelector('a[href*="/messenger_media/"]');
    if (imageLink) {
      const img = imageLink.querySelector('img');
      if (img) {
        console.log("New image message found:", img.src);
        uploadImage(img.src);
      }
    }
  }

  // Start observing for new messages.
  function startObserver() {
    if (observerActive) return;

    // Find the container that holds messages.
    const messagesContainer = document.querySelector('[aria-label="Messages"]') || document.body;

    observer = new MutationObserver(mutations => {
      mutations.forEach(mutation => {
        mutation.addedNodes.forEach(node => {
          if (node.nodeType === Node.ELEMENT_NODE) {
            if (node.matches('[data-pagelet="MWMessageRow"]')) {
              processImageMessage(node);
            } else {
              const newMessages = node.querySelectorAll('[data-pagelet="MWMessageRow"]');
              newMessages.forEach(msg => processImageMessage(msg));
            }
          }
        });
      });
    });
  
    observer.observe(messagesContainer, { childList: true, subtree: true });
    observerActive = true;
    console.log("Observer started. Only new image messages will be processed.");
  }

  // Listen for messages from the extension's popup.
  chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg.action === "enableUploader") {
      startObserver();
      sendResponse({status: "enabled"});
    }
  });
})();