function uploadVideo() {
    console.log("------upload button clicked---")
    

    // const baseLink = "http://localhost:8001"
    const baseLink = "http://20.50.56.47:8001"
    var formData = new FormData();
    const videoInput = document.getElementById('videoInput');
    const videoFile = videoInput.files[0];
    formData.append('file', videoFile);
    const downloadBtn = document.getElementById('downloadButton')   
    downloadBtn.style.display = 'none';     

    if (videoFile){
            
        var submitDiv=document.getElementById("submitdiv");
        submitDiv.innerHTML = "<span class='spinner-border spinner-border-sm' role='status' aria-hidden='true'></span>";

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.text())
        .then(res => {
            // Handle the response
            console.log("-----upload link--")
            console.log(res);

            const filePath =  res.replace(/\\/g, "\\\\");   
            fetch('/run', { 
                method: 'POST', 
                body: JSON.stringify({ path: filePath }), 
                headers: { 'Content-Type': 'application/json' } 
            })
            .then(response => response.json())  
            .then(data => {  

                submitDiv.innerHTML = '<div id="submitdiv">Upload</div>';
                // Get the video URL from the response  
                const videoUrl = baseLink + data.video_url;  
          
                // Get the download link element  
                const downloadLink = document.getElementById('downloadLink');  
          
                // Set the href attribute of the download link  
                downloadLink.href = videoUrl;  
          
                // Set the download attribute of the download link (this will suggest a filename when downloading)  
                const now = new Date();
                const year = now.getFullYear();
                const month = String(now.getMonth() + 1).padStart(2, '0');
                const day = String(now.getDate()).padStart(2, '0');
                const hours = String(now.getHours()).padStart(2, '0');
                const minutes = String(now.getMinutes()).padStart(2, '0');
                const seconds = String(now.getSeconds()).padStart(2, '0');

                const filename = `${year}${month}${day}_${hours}${minutes}${seconds}.mp4`;
                downloadLink.download = filename;  
          
                // Unhide the download link  
                // downloadLink.style.display = 'block';  
          
                // Bind the download function to the button  

                
                downloadBtn.style.display = 'block';
                downloadBtn.addEventListener('click', function() {  
                    downloadLink.click();  
                });  
            })
            .catch((error) => console.error('Error:', error));


           
            // container.innerHTML = '';
            // logdiv.innerHTML = alert_msg
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }
    else{
        console.log("video is not selected")
    }

   

}
