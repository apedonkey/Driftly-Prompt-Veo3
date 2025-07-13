// Driftly AI Video Studio Frontend

let currentJobId = null;

// Override fetch to use CSRF protection for API calls
// Only do this if secureFetch is available
if (typeof secureFetch !== 'undefined') {
    const origFetch = window.originalFetch || window.fetch;
    window.fetch = function(url, options = {}) {
        // Only intercept API calls, and avoid recursion
        if (url.startsWith('/api/') && !url.includes('/csrf-token')) {
            return secureFetch(url, options);
        }
        return origFetch(url, options);
    };
}
let statusCheckInterval = null;
let progressTimeouts = [];

// Check for first time setup
document.addEventListener('DOMContentLoaded', function() {
    checkFirstTimeSetup();
    loadStats();
    setupAutoExpand();
    
    // Auto-expand textarea
    const textarea = document.getElementById('quickTopic');
    if (textarea) {
        textarea.addEventListener('input', function() {
            autoExpand(this);
        });
    }
    
    // Handle image preview
    const imageInput = document.getElementById('imageInput');
    if (imageInput) {
        imageInput.addEventListener('change', handleImagePreview);
    }
    
    // Handle schedule image preview
    const scheduleImageInput = document.getElementById('scheduleImageInput');
    if (scheduleImageInput) {
        scheduleImageInput.addEventListener('change', handleScheduleImagePreview);
    }
    
    // Load scheduled videos if sheet is configured
    if (localStorage.getItem('spreadsheetId')) {
        loadScheduledVideos();
    }
    
    // Set minimum date to today for scheduling
    const scheduleDate = document.getElementById('scheduleDate');
    if (scheduleDate) {
        scheduleDate.min = new Date().toISOString().split('T')[0];
    }
    
    // Handle cancel confirmation button
    const confirmCancelBtn = document.getElementById('confirmCancelBtn');
    if (confirmCancelBtn) {
        confirmCancelBtn.addEventListener('click', cancelScheduledVideo);
    }
});

function handleImagePreview(event) {
    const files = event.target.files;
    const previewContainer = document.getElementById('imagePreview');
    const previewGrid = document.getElementById('imagePreviewGrid');
    
    if (files.length > 0) {
        previewContainer.style.display = 'block';
        previewGrid.innerHTML = '';
        
        // Store files array for manipulation
        window.selectedFiles = Array.from(files);
        
        window.selectedFiles.forEach((file, index) => {
            const reader = new FileReader();
            reader.onload = function(e) {
                const col = document.createElement('div');
                col.className = 'col-3';
                col.innerHTML = `
                    <div class="position-relative image-preview-item">
                        <img src="${escapeHtml(e.target.result)}" class="img-fluid rounded" alt="Reference ${index + 1}">
                        <button class="btn btn-danger btn-sm image-remove-btn" onclick="removeImage(${index})" title="Remove image">
                            <i class="bi bi-x"></i>
                        </button>
                        <small class="d-block text-center mt-1">Image ${index + 1}</small>
                    </div>
                `;
                previewGrid.appendChild(col);
            };
            reader.readAsDataURL(file);
        });
    } else {
        previewContainer.style.display = 'none';
    }
}

function removeImage(index) {
    // Remove the file from our array
    window.selectedFiles.splice(index, 1);
    
    // Update the file input
    const imageInput = document.getElementById('imageInput');
    const dt = new DataTransfer();
    
    // Add remaining files to DataTransfer
    window.selectedFiles.forEach(file => {
        dt.items.add(file);
    });
    
    // Update the input files
    imageInput.files = dt.files;
    
    // Trigger preview update
    handleImagePreview({ target: imageInput });
}

function handleScheduleImagePreview(event) {
    const files = event.target.files;
    const previewContainer = document.getElementById('scheduleImagePreview');
    const previewGrid = document.getElementById('scheduleImagePreviewGrid');
    
    if (files.length > 0) {
        previewContainer.style.display = 'block';
        previewGrid.innerHTML = '';
        
        // Store files array for manipulation
        window.scheduleSelectedFiles = Array.from(files);
        
        window.scheduleSelectedFiles.forEach((file, index) => {
            const reader = new FileReader();
            reader.onload = function(e) {
                const col = document.createElement('div');
                col.className = 'col-3';
                col.innerHTML = `
                    <div class="position-relative image-preview-item">
                        <img src="${escapeHtml(e.target.result)}" class="img-fluid rounded" alt="Reference ${index + 1}">
                        <button class="btn btn-danger btn-sm image-remove-btn" onclick="removeScheduleImage(${index})" title="Remove image">
                            <i class="bi bi-x"></i>
                        </button>
                        <small class="d-block text-center mt-1">Image ${index + 1}</small>
                    </div>
                `;
                previewGrid.appendChild(col);
            };
            reader.readAsDataURL(file);
        });
    } else {
        previewContainer.style.display = 'none';
    }
}

function removeScheduleImage(index) {
    // Remove the file from our array
    window.scheduleSelectedFiles.splice(index, 1);
    
    // Update the file input
    const scheduleImageInput = document.getElementById('scheduleImageInput');
    const dt = new DataTransfer();
    
    // Add remaining files to DataTransfer
    window.scheduleSelectedFiles.forEach(file => {
        dt.items.add(file);
    });
    
    // Update the input files
    scheduleImageInput.files = dt.files;
    
    // Trigger preview update
    handleScheduleImagePreview({ target: scheduleImageInput });
}

// Test function for debugging
window.testScriptPreview = function() {
    const testData = {
        title: "Test Video Title",
        visual_prompts: "This is a test visual prompt that should appear in the textarea. It includes detailed scene description with camera movements, lighting setup, and all the cinematic details that Grok would generate.",
        camera_work: "Slow dolly in, 85mm lens, shallow DOF",
        lighting: "Golden hour with rim lighting",
        style_keywords: ["cinematic", "8K", "photorealistic"],
        final_veo3_prompt: "This is the final prompt that will be sent to Veo 3, including all enhancements and style keywords."
    };
    showPromptPreview(testData);
};

function setupAutoExpand() {
    const textareas = document.querySelectorAll('.auto-expand');
    textareas.forEach(textarea => {
        textarea.addEventListener('input', function() {
            autoExpand(this);
        });
        // Initial adjustment
        autoExpand(textarea);
    });
}

function autoExpand(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
}

function checkFirstTimeSetup() {
    const hasKeys = localStorage.getItem('grokApiKey') && localStorage.getItem('falApiKey');
    
    if (!hasKeys) {
        document.getElementById('firstTimeSetup').style.display = 'flex';
    } else {
        loadRecentVideos();
    }
}

function toggleYoutubeFields() {
    const checkbox = document.getElementById('setupYoutube');
    const fields = document.getElementById('youtubeFields');
    fields.style.display = checkbox.checked ? 'block' : 'none';
}

function togglePasswordVisibility(inputId, button) {
    const input = document.getElementById(inputId);
    const icon = button.querySelector('i');
    
    if (input.type === 'password') {
        input.type = 'text';
        icon.classList.remove('bi-eye');
        icon.classList.add('bi-eye-slash');
    } else {
        input.type = 'password';
        icon.classList.remove('bi-eye-slash');
        icon.classList.add('bi-eye');
    }
}

function saveSetup() {
    const grokKey = document.getElementById('setupGrokKey').value.trim();
    const falKey = document.getElementById('setupFalKey').value.trim();
    const sheetId = document.getElementById('setupSheetId').value.trim();
    const useYoutube = document.getElementById('setupYoutube').checked;
    const youtubeSecrets = document.getElementById('youtubeClientSecrets').value.trim();
    
    if (!grokKey || !falKey) {
        alert('Please enter both API keys');
        return;
    }
    
    if (useYoutube && !youtubeSecrets) {
        alert('Please paste your YouTube client secrets JSON');
        return;
    }
    
    // Save to localStorage
    localStorage.setItem('grokApiKey', grokKey);
    localStorage.setItem('falApiKey', falKey);
    if (sheetId) localStorage.setItem('spreadsheetId', sheetId);
    localStorage.setItem('useYoutube', useYoutube);
    if (youtubeSecrets) {
        try {
            // Validate JSON
            JSON.parse(youtubeSecrets);
            localStorage.setItem('youtubeClientSecrets', youtubeSecrets);
        } catch (e) {
            alert('Invalid JSON format for YouTube credentials');
            return;
        }
    }
    
    // Reset unsaved changes flag
    setupHasUnsavedChanges = false;
    
    // Hide setup
    document.getElementById('firstTimeSetup').style.display = 'none';
    
    // Reload page to apply settings
    location.reload();
}

function showSetup() {
    document.getElementById('firstTimeSetup').style.display = 'flex';
    
    // Pre-fill existing values
    document.getElementById('setupGrokKey').value = localStorage.getItem('grokApiKey') || '';
    document.getElementById('setupFalKey').value = localStorage.getItem('falApiKey') || '';
    document.getElementById('setupSheetId').value = localStorage.getItem('spreadsheetId') || '';
    
    const useYoutube = localStorage.getItem('useYoutube') === 'true';
    document.getElementById('setupYoutube').checked = useYoutube;
    
    if (useYoutube) {
        document.getElementById('youtubeFields').style.display = 'block';
        document.getElementById('youtubeClientSecrets').value = localStorage.getItem('youtubeClientSecrets') || '';
    }
}

function showSetupModal() {
    // This is called from the missing API keys modal
    showSetup();
}

// Track if setup form has unsaved changes
let setupHasUnsavedChanges = false;

function trackSetupChanges() {
    setupHasUnsavedChanges = true;
}

function closeSetup() {
    // Check if there are unsaved changes
    const currentGrokKey = document.getElementById('setupGrokKey').value;
    const currentFalKey = document.getElementById('setupFalKey').value;
    const savedGrokKey = localStorage.getItem('grokApiKey') || '';
    const savedFalKey = localStorage.getItem('falApiKey') || '';
    
    // Check if user has entered new values that haven't been saved
    const hasUnsavedKeys = (currentGrokKey && currentGrokKey !== savedGrokKey) || 
                          (currentFalKey && currentFalKey !== savedFalKey);
    
    if (hasUnsavedKeys) {
        // Show unsaved changes modal
        const unsavedModal = new bootstrap.Modal(document.getElementById('unsavedSetupModal'));
        unsavedModal.show();
    } else {
        document.getElementById('firstTimeSetup').style.display = 'none';
        setupHasUnsavedChanges = false;
    }
}

function continueSetup() {
    // Close the unsaved modal and keep setup open
    const unsavedModal = bootstrap.Modal.getInstance(document.getElementById('unsavedSetupModal'));
    unsavedModal.hide();
}

function confirmCloseSetup() {
    // Close both modals
    const unsavedModal = bootstrap.Modal.getInstance(document.getElementById('unsavedSetupModal'));
    unsavedModal.hide();
    document.getElementById('firstTimeSetup').style.display = 'none';
    setupHasUnsavedChanges = false;
}

function showInstructions() {
    const modal = new bootstrap.Modal(document.getElementById('instructionsModal'));
    modal.show();
}

async function getRandomIdea(textareaId) {
    const textarea = document.getElementById(textareaId);
    const originalPlaceholder = textarea.placeholder;
    
    // Show loading state
    textarea.placeholder = 'Getting a random idea from Grok...';
    textarea.disabled = true;
    
    try {
        const grokKey = localStorage.getItem('grokApiKey');
        if (!grokKey) {
            showSetup();
            textarea.placeholder = originalPlaceholder;
            textarea.disabled = false;
            return;
        }
        
        const response = await fetch('/api/random-idea', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                grokApiKey: grokKey
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Animate the text appearance
            textarea.value = '';
            const idea = data.idea;
            let index = 0;
            
            const typeWriter = setInterval(() => {
                if (index < idea.length) {
                    textarea.value += idea[index];
                    index++;
                    // Auto-expand if needed
                    if (textarea.classList.contains('auto-expand')) {
                        autoExpand(textarea);
                    }
                } else {
                    clearInterval(typeWriter);
                }
            }, 20);
        } else {
            alert('Failed to get random idea: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        alert('Error getting random idea: ' + error.message);
    } finally {
        textarea.placeholder = originalPlaceholder;
        textarea.disabled = false;
    }
}

let pendingVideoData = null;

async function generateVideo() {
    const topic = document.getElementById('quickTopic').value.trim();
    const imageInput = document.getElementById('imageInput');
    const imageFiles = window.selectedFiles || Array.from(imageInput.files); // Use selectedFiles if available
    const duration = parseInt(document.getElementById('videoDuration').value);
    const videoStyle = document.getElementById('videoStyle').value;
    
    if (!topic) {
        alert('Please enter a topic');
        return;
    }
    
    // Check API keys
    const grokKey = localStorage.getItem('grokApiKey');
    const falKey = localStorage.getItem('falApiKey');
    
    if (!grokKey || !falKey) {
        // Show missing API keys modal
        const missingKeysModal = new bootstrap.Modal(document.getElementById('missingApiKeysModal'));
        missingKeysModal.show();
        return;
    }
    
    // Disable the generate button
    const generateBtn = document.getElementById('generateVideoBtn');
    if (generateBtn) {
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Generating...';
    }
    
    // First, generate the script and get prompt preview
    document.getElementById('progressSection').style.display = 'block';
    document.getElementById('resultSection').style.display = 'none';
    document.getElementById('progressText').textContent = 'Initializing...';
    updateProgressBar(0);
    
    // Animate to 10% after a brief delay
    setTimeout(() => {
        document.getElementById('progressText').textContent = 'Generating script with Grok...';
        updateProgressBar(10);
    }, 300);
    
    // Clear any existing progress timeouts
    progressTimeouts.forEach(timeout => clearTimeout(timeout));
    progressTimeouts = [];
    
    // Simulate progress during script generation
    progressTimeouts.push(setTimeout(() => updateProgressBar(30), 1000));
    progressTimeouts.push(setTimeout(() => updateProgressBar(50), 2000));
    progressTimeouts.push(setTimeout(() => {
        document.getElementById('progressText').textContent = 'Analyzing content...';
        updateProgressBar(70);
    }, 3000));
    progressTimeouts.push(setTimeout(() => updateProgressBar(85), 4000));
    
    try {
        // Store data for later
        pendingVideoData = {
            topic: topic,
            imageFiles: imageFiles, // Now storing multiple files
            duration: duration,
            videoStyle: videoStyle,
            grokApiKey: grokKey,
            falApiKey: falKey,
            useYoutube: localStorage.getItem('useYoutube') === 'true',
            youtubeClientSecrets: localStorage.getItem('youtubeClientSecrets') || ''
        };
        
        // Create FormData to send images to Grok for analysis
        const scriptFormData = new FormData();
        scriptFormData.append('topic', topic);
        scriptFormData.append('duration', duration);
        scriptFormData.append('videoStyle', videoStyle);
        scriptFormData.append('grokApiKey', grokKey);
        
        // Add images for Grok to analyze
        if (imageFiles && imageFiles.length > 0) {
            imageFiles.forEach((file) => {
                scriptFormData.append('images', file);
            });
        }
        
        // Request script generation with images
        const response = await fetch('/api/generate-script', {
            method: 'POST',
            body: scriptFormData
        });
        
        const data = await response.json();
        console.log('Generate script response:', data); // Debug log
        
        if (data.success) {
            // Check if script_data exists
            if (!data.script_data) {
                console.error('No script_data in response!');
                showError('No script data received from server');
                return;
            }
            
            // Clear any pending progress timeouts
            progressTimeouts.forEach(timeout => clearTimeout(timeout));
            progressTimeouts = [];
            
            // Complete the progress bar
            document.getElementById('progressText').textContent = 'Script generated successfully!';
            updateProgressBar(100);
            
            // Hide progress and show modal after animation completes
            setTimeout(() => {
                document.getElementById('progressSection').style.display = 'none';
                updateProgressBar(0); // Reset for next phase
                // Show prompt preview modal
                showPromptPreview(data.script_data);
            }, 800);
        } else {
            showError(data.error || 'Unknown error occurred');
            enableGenerateButton();
        }
    } catch (error) {
        showError('Failed to generate script');
        enableGenerateButton();
    }
}

function showPromptPreview(scriptData) {
    try {
        console.log('Script data received:', scriptData); // Debug log
        console.log('Script data keys:', Object.keys(scriptData)); // Debug keys
        console.log('visual_prompts value:', scriptData.visual_prompts); // Debug visual_prompts
        console.log('final_veo3_prompt value:', scriptData.final_veo3_prompt); // Debug final prompt
        console.log('camera_work type:', typeof scriptData.camera_work, 'value:', scriptData.camera_work); // Debug camera_work
        console.log('lighting type:', typeof scriptData.lighting, 'value:', scriptData.lighting); // Debug lighting
        
        // Remove any schedule info if present
        const existingScheduleInfo = document.querySelector('#promptPreviewModal .alert-info');
        if (existingScheduleInfo) {
            existingScheduleInfo.remove();
        }
        
        // Reset button to generate video (in case it was changed for scheduling)
        const generateBtn = document.querySelector('#promptPreviewModal .modal-footer .btn-primary');
        if (generateBtn) {
            generateBtn.innerHTML = '<i class="bi bi-check-circle"></i> Generate Video';
            generateBtn.onclick = proceedWithGeneration;
        }
        
        // Populate modal with script data
        const titleInput = document.getElementById('previewTitle');
        if (titleInput) titleInput.value = scriptData.title || '';
        
        // Use the final prompt if available, otherwise visual_prompts
        const visualPrompt = scriptData.final_veo3_prompt || scriptData.visual_prompts || '';
        console.log('Visual prompt to display:', visualPrompt); // Debug what we're showing
        const promptTextarea = document.getElementById('previewPrompt');
        if (promptTextarea) promptTextarea.value = visualPrompt;
        
        // Set camera work
        const cameraTextarea = document.getElementById('previewCamera');
        if (cameraTextarea) {
            let cameraWork = scriptData.camera_work || 'Camera setup not specified';
            // Handle case where camera_work might be an object
            if (typeof cameraWork === 'object' && cameraWork !== null) {
                // If it's an array, join the elements
                if (Array.isArray(cameraWork)) {
                    cameraWork = cameraWork.join(', ');
                } else {
                    // For other objects, try to extract meaningful text
                    if (cameraWork.text || cameraWork.value || cameraWork.description) {
                        cameraWork = cameraWork.text || cameraWork.value || cameraWork.description;
                    } else if (Object.keys(cameraWork).length === 0) {
                        // Empty object
                        cameraWork = 'Camera setup not specified';
                    } else {
                        // Extract values from object
                        const values = Object.values(cameraWork).filter(v => v && typeof v === 'string');
                        cameraWork = values.length > 0 ? values.join(', ') : 'Camera setup not specified';
                    }
                }
            }
            // Clean up any remaining JSON artifacts
            cameraWork = String(cameraWork).replace(/[{}"]/g, '').trim();
            cameraTextarea.value = cameraWork || 'Camera setup not specified';
        }
        
        // Set lighting
        const lightingTextarea = document.getElementById('previewLighting');
        if (lightingTextarea) {
            let lighting = scriptData.lighting || 'Lighting not specified';
            // Handle case where lighting might be an object
            if (typeof lighting === 'object' && lighting !== null) {
                // If it's an array, join the elements
                if (Array.isArray(lighting)) {
                    lighting = lighting.join(', ');
                } else {
                    // For other objects, try to extract meaningful text
                    if (lighting.text || lighting.value || lighting.description) {
                        lighting = lighting.text || lighting.value || lighting.description;
                    } else if (Object.keys(lighting).length === 0) {
                        // Empty object
                        lighting = 'Lighting not specified';
                    } else {
                        // Extract values from object
                        const values = Object.values(lighting).filter(v => v && typeof v === 'string');
                        lighting = values.length > 0 ? values.join(', ') : 'Lighting not specified';
                    }
                }
            }
            // Clean up any remaining JSON artifacts
            lighting = String(lighting).replace(/[{}"]/g, '').trim();
            lightingTextarea.value = lighting || 'Lighting not specified';
        }
        
        // Handle style keywords - could be array or string
        let keywords = '';
        if (Array.isArray(scriptData.style_keywords)) {
            keywords = scriptData.style_keywords.join(', ');
        } else if (scriptData.style_keywords) {
            keywords = scriptData.style_keywords;
        }
        const keywordsInput = document.getElementById('previewKeywords');
        if (keywordsInput) keywordsInput.value = keywords || 'No style keywords specified';
        
        // Store script data - initialize if needed
        if (!pendingVideoData) {
            pendingVideoData = {};
        }
        pendingVideoData.scriptData = scriptData;
        
        // Show modal
        const modalElement = document.getElementById('promptPreviewModal');
        if (modalElement) {
            const modal = new bootstrap.Modal(modalElement);
            modal.show();
            
            // Re-enable button when modal is closed without proceeding
            modalElement.addEventListener('hidden.bs.modal', function onModalHidden() {
                // Only re-enable if we're not in the middle of video generation
                if (!currentJobId || !statusCheckInterval) {
                    enableGenerateButton();
                }
                // Remove the event listener after it fires
                modalElement.removeEventListener('hidden.bs.modal', onModalHidden);
            });
        } else {
            console.error('Modal element not found!');
            alert('Error: Preview modal not found. Please refresh the page.');
            enableGenerateButton();
        }
    } catch (error) {
        console.error('Error showing prompt preview:', error);
        alert('Error showing preview: ' + error.message);
    }
}

async function proceedWithGeneration() {
    // Close modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('promptPreviewModal'));
    modal.hide();
    
    // Update script data with edited prompt
    pendingVideoData.scriptData.visual_prompts = document.getElementById('previewPrompt').value;
    
    // Show progress
    document.getElementById('progressSection').style.display = 'block';
    document.getElementById('progressText').textContent = 'Preparing video generation...';
    updateProgressBar(25);
    
    // Update after a brief delay
    setTimeout(() => {
        document.getElementById('progressText').textContent = 'Creating video with Veo 3...';
        updateProgressBar(35);
    }, 500);
    
    try {
        const formData = new FormData();
        formData.append('topic', pendingVideoData.topic);
        formData.append('grokApiKey', pendingVideoData.grokApiKey);
        formData.append('falApiKey', pendingVideoData.falApiKey);
        formData.append('useYoutube', pendingVideoData.useYoutube);
        formData.append('youtubeClientSecrets', pendingVideoData.youtubeClientSecrets);
        formData.append('duration', pendingVideoData.duration);
        formData.append('scriptData', JSON.stringify(pendingVideoData.scriptData));
        
        // Append multiple images
        if (pendingVideoData.imageFiles && pendingVideoData.imageFiles.length > 0) {
            pendingVideoData.imageFiles.forEach((file, index) => {
                formData.append(`images`, file);
            });
        }
        
        const response = await fetch('/api/generate-video', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentJobId = data.job_id;
            startStatusChecking();
        } else {
            showError(data.error);
            enableGenerateButton();
        }
    } catch (error) {
        showError('Failed to start video generation');
        enableGenerateButton();
    }
}

function startStatusChecking() {
    statusCheckInterval = setInterval(checkJobStatus, 2000);
}

async function checkJobStatus() {
    if (!currentJobId) return;
    
    try {
        const response = await fetch(`/api/status/${currentJobId}`);
        const data = await response.json();
        
        if (data.success) {
            const job = data.job;
            
            // Update progress text
            document.getElementById('progressText').textContent = job.progress;
            
            // Update progress bar with smoother transitions
            if (job.progress.includes('Initializing')) {
                updateProgressBar(5);
            } else if (job.progress.includes('Generating script')) {
                updateProgressBar(15);
            } else if (job.progress.includes('script')) {
                updateProgressBar(30);
            } else if (job.progress.includes('Creating video')) {
                updateProgressBar(45);
            } else if (job.progress.includes('Processing')) {
                updateProgressBar(55);
            } else if (job.progress.includes('video')) {
                updateProgressBar(70);
            } else if (job.progress.includes('Finalizing')) {
                updateProgressBar(85);
            } else if (job.progress.includes('YouTube') || job.progress.includes('Saving')) {
                updateProgressBar(95);
            }
            
            // Handle completion
            if (job.status === 'completed') {
                updateProgressBar(100);
                document.getElementById('progressText').textContent = 'Complete!';
                clearInterval(statusCheckInterval);
                
                // Show success after a brief delay
                setTimeout(() => {
                    showSuccess(job);
                    loadRecentVideos();
                    updateTodayCount();
                    enableGenerateButton();
                }, 500);
            } else if (job.status === 'error') {
                clearInterval(statusCheckInterval);
                showError(job.error);
                enableGenerateButton();
            }
        }
    } catch (error) {
        console.error('Status check failed:', error);
    }
}

function updateProgressBar(percent) {
    const progressBar = document.getElementById('progressBar');
    progressBar.style.width = percent + '%';
    progressBar.setAttribute('aria-valuenow', percent);
}

function enableGenerateButton() {
    const generateBtn = document.getElementById('generateVideoBtn');
    if (generateBtn) {
        generateBtn.disabled = false;
        generateBtn.innerHTML = '<i class="bi bi-stars"></i> Generate Video';
    }
}

function updateScheduleProgressBar(percent) {
    const progressBar = document.getElementById('scheduleProgressBar');
    if (progressBar) {
        progressBar.style.width = percent + '%';
        progressBar.setAttribute('aria-valuenow', percent);
    }
}

function showSuccess(job) {
    document.getElementById('progressSection').style.display = 'none';
    document.getElementById('resultSection').style.display = 'block';
    
    document.getElementById('resultTitle').textContent = job.video_title || 'Video Created!';
    document.getElementById('resultMessage').textContent = job.video_url ? 
        'Your video has been uploaded to YouTube.' : 
        'Your video has been saved locally.';
    
    if (job.video_url) {
        const link = document.getElementById('resultLink');
        link.href = job.video_url;
        link.style.display = 'inline-block';
    }
}

function showError(message) {
    document.getElementById('progressSection').style.display = 'none';
    document.getElementById('resultSection').style.display = 'block';
    
    document.querySelector('.result-icon i').className = 'bi bi-x-circle-fill text-danger';
    document.getElementById('resultTitle').textContent = 'Error';
    document.getElementById('resultMessage').textContent = message;
    document.getElementById('resultLink').style.display = 'none';
}

function resetForm() {
    document.getElementById('quickTopic').value = '';
    document.getElementById('resultSection').style.display = 'none';
    document.querySelector('.result-icon i').className = 'bi bi-check-circle-fill text-success';
    
    // Clear image selection
    document.getElementById('imageInput').value = '';
    document.getElementById('imagePreview').style.display = 'none';
    window.selectedFiles = [];
    
    // Reset progress bar
    updateProgressBar(0);
    
    // Re-enable generate button
    enableGenerateButton();
    
    // Clear current job
    currentJobId = null;
}

async function loadRecentVideos() {
    try {
        const response = await fetch('/api/recent-videos');
        const data = await response.json();
        
        if (data.success) {
            const container = document.getElementById('recentVideosList');
            container.innerHTML = '';
            
            if (data.videos.length === 0) {
                container.innerHTML = '<div class="text-center text-muted"><i class="bi bi-film"></i> No videos yet</div>';
                return;
            }
            
            data.videos.forEach(video => {
                const item = document.createElement('div');
                item.className = 'video-item';
                
                const date = new Date(video.created_at || video['Published Date']);
                const timeAgo = getTimeAgo(date);
                
                item.innerHTML = `
                    <h6>${escapeHtml(video.title || video.Title)}</h6>
                    <small>${escapeHtml(video.topic || video.Topic)}</small>
                    <div class="d-flex justify-content-between mt-2">
                        <small class="text-muted">${timeAgo}</small>
                        ${video.video_url || video['Video URL'] ? 
                            `<a href="${video.video_url || video['Video URL']}" target="_blank" class="btn btn-sm btn-outline-primary">
                                <i class="bi bi-play-circle"></i> Watch
                            </a>` : 
                            '<span class="badge bg-secondary">Local Only</span>'
                        }
                    </div>
                `;
                
                container.appendChild(item);
            });
        }
    } catch (error) {
        console.error('Failed to load recent videos:', error);
    }
}

async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('totalVideos').textContent = data.total || 0;
            document.getElementById('totalViews').textContent = data.views || 0;
            document.getElementById('todayVideos').textContent = data.today || 0;
        }
    } catch (error) {
        // Stats are optional, don't show error
    }
}

function updateTodayCount() {
    const current = parseInt(document.getElementById('todayVideos').textContent) || 0;
    document.getElementById('todayVideos').textContent = current + 1;
}

function getTimeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);
    
    if (seconds < 60) return 'just now';
    if (seconds < 3600) return Math.floor(seconds / 60) + ' min ago';
    if (seconds < 86400) return Math.floor(seconds / 3600) + ' hours ago';
    return Math.floor(seconds / 86400) + ' days ago';
}

// Debug function to test script preview
async function testScriptPreview() {
    try {
        const response = await fetch('/api/test-script');
        const data = await response.json();
        
        if (data.success) {
            console.log('Test script data:', data.script_data);
            showPromptPreview(data.script_data);
        }
    } catch (error) {
        console.error('Test failed:', error);
    }
}

// Store pending schedule data
let pendingScheduleData = null;

// Scheduling Functions
async function scheduleVideo() {
    const date = document.getElementById('scheduleDate').value;
    const time = document.getElementById('scheduleTime').value;
    const topic = document.getElementById('scheduleTopicInput').value.trim();
    const duration = document.getElementById('scheduleDuration').value;
    const style = document.getElementById('scheduleStyle').value;
    const scheduleImageInput = document.getElementById('scheduleImageInput');
    const imageFiles = window.scheduleSelectedFiles || Array.from(scheduleImageInput.files);
    
    if (!date || !time || !topic) {
        alert('Please fill in all scheduling fields');
        return;
    }
    
    if (!localStorage.getItem('spreadsheetId')) {
        alert('Please configure Google Sheets in the setup to use scheduling');
        showSetup();
        return;
    }
    
    // Check API key
    const grokKey = localStorage.getItem('grokApiKey');
    if (!grokKey) {
        showSetup();
        return;
    }
    
    // Combine date and time
    const scheduledDateTime = new Date(`${date}T${time}`);
    
    if (scheduledDateTime <= new Date()) {
        alert('Please select a future date and time');
        return;
    }
    
    // Store schedule data for later
    pendingScheduleData = {
        topic,
        scheduledTime: scheduledDateTime.toISOString(),
        duration: parseInt(duration),
        style,
        date,
        time,
        imageFiles: imageFiles // Store image files
    };
    
    // Show progress in schedule section
    document.getElementById('scheduleProgressSection').style.display = 'block';
    document.getElementById('scheduleProgressText').textContent = 'Initializing...';
    updateScheduleProgressBar(0);
    
    // Animate progress
    setTimeout(() => {
        document.getElementById('scheduleProgressText').textContent = 'Generating script preview with Grok...';
        updateScheduleProgressBar(10);
    }, 300);
    
    // Clear any existing progress timeouts
    progressTimeouts.forEach(timeout => clearTimeout(timeout));
    progressTimeouts = [];
    
    // Simulate progress during script generation
    progressTimeouts.push(setTimeout(() => updateScheduleProgressBar(30), 1000));
    progressTimeouts.push(setTimeout(() => updateScheduleProgressBar(50), 2000));
    progressTimeouts.push(setTimeout(() => {
        document.getElementById('scheduleProgressText').textContent = 'Analyzing content...';
        updateScheduleProgressBar(70);
    }, 3000));
    progressTimeouts.push(setTimeout(() => updateScheduleProgressBar(85), 4000));
    
    try {
        // Create FormData to send images
        const scriptFormData = new FormData();
        scriptFormData.append('topic', topic);
        scriptFormData.append('duration', duration);
        scriptFormData.append('videoStyle', style);
        scriptFormData.append('grokApiKey', grokKey);
        
        // Add images if selected
        if (imageFiles && imageFiles.length > 0) {
            imageFiles.forEach((file) => {
                scriptFormData.append('images', file);
            });
        }
        
        // Generate script preview using the same endpoint
        const response = await fetch('/api/generate-script', {
            method: 'POST',
            body: scriptFormData
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Clear any pending progress timeouts
            progressTimeouts.forEach(timeout => clearTimeout(timeout));
            progressTimeouts = [];
            
            // Update progress
            updateScheduleProgressBar(100);
            document.getElementById('scheduleProgressText').textContent = 'Script ready!';
            
            // Hide progress after a short delay
            setTimeout(() => {
                document.getElementById('scheduleProgressSection').style.display = 'none';
                updateScheduleProgressBar(0); // Reset for next time
                
                // Store script data with schedule data
                pendingScheduleData.scriptData = data.script_data;
                
                // Show prompt preview modal for scheduling
                showSchedulePromptPreview(data.script_data);
            }, 800);
        } else {
            document.getElementById('scheduleProgressSection').style.display = 'none';
            alert('Failed to generate script: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        document.getElementById('scheduleProgressSection').style.display = 'none';
        alert('Failed to generate script preview: ' + error.message);
    }
}

async function loadScheduledVideos() {
    if (!localStorage.getItem('spreadsheetId')) {
        return;
    }
    
    try {
        const response = await fetch('/api/scheduled-videos');
        const data = await response.json();
        
        if (data.success) {
            displayScheduledVideos(data.videos);
        }
    } catch (error) {
        console.error('Failed to load scheduled videos:', error);
    }
}

function displayScheduledVideos(videos) {
    const container = document.getElementById('scheduledVideosList');
    
    if (!videos || videos.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted">
                <i class="bi bi-calendar-x"></i> No scheduled videos
            </div>
        `;
        return;
    }
    
    container.innerHTML = videos.map((video, index) => {
        const scheduledDate = new Date(video.scheduledTime);
        const now = new Date();
        const isPast = scheduledDate < now;
        const isToday = scheduledDate.toDateString() === now.toDateString();
        
        return `
            <div class="scheduled-video-item ${isPast ? 'past-due' : ''} ${isToday ? 'today' : ''}">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <h6 class="mb-1">${video.topic}</h6>
                        <small class="text-muted">
                            <i class="bi bi-calendar3"></i> ${scheduledDate.toLocaleDateString()}
                            <i class="bi bi-clock ms-2"></i> ${scheduledDate.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                        </small>
                        <div class="mt-1">
                            <span class="badge bg-secondary">${video.duration}s</span>
                            <span class="badge bg-info ms-1">${video.style}</span>
                            <span class="badge ${video.status === 'Pending' ? 'bg-warning' : 'bg-success'} ms-1">
                                ${video.status}
                            </span>
                        </div>
                    </div>
                    <div class="ms-2">
                        ${video.status === 'Pending' ? `
                            <button class="btn btn-sm btn-danger" onclick="showCancelModal('${video.id}', '${video.topic}', '${scheduledDate.toISOString()}')" title="Cancel">
                                <i class="bi bi-x-circle"></i>
                            </button>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

let pendingCancelVideoId = null;

function showCancelModal(videoId, topic, scheduledTime) {
    // Store the video ID for later
    pendingCancelVideoId = videoId;
    
    // Update modal with video details
    const detailsDiv = document.getElementById('cancelVideoDetails');
    const scheduleDate = new Date(scheduledTime);
    
    detailsDiv.innerHTML = `
        <h6 class="mb-2">${escapeHtml(topic)}</h6>
        <small class="text-muted">
            Scheduled for: ${scheduleDate.toLocaleDateString()} at ${scheduleDate.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
        </small>
    `;
    
    // Show the modal
    const cancelModal = new bootstrap.Modal(document.getElementById('cancelScheduleModal'));
    cancelModal.show();
}

async function cancelScheduledVideo() {
    if (!pendingCancelVideoId) return;
    
    try {
        const response = await fetch(`/api/cancel-scheduled/${pendingCancelVideoId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Hide the modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('cancelScheduleModal'));
            modal.hide();
            
            // Reload the scheduled videos
            loadScheduledVideos();
            
            // Reset the pending ID
            pendingCancelVideoId = null;
        } else {
            alert('Failed to cancel scheduled video');
        }
    } catch (error) {
        alert('Error canceling video: ' + error.message);
    }
}

function clearCancelledVideos() {
    // Show confirmation modal
    const confirmModal = new bootstrap.Modal(document.getElementById('clearCancelledConfirmModal'));
    confirmModal.show();
}

async function confirmClearCancelled() {
    // Hide confirmation modal
    const confirmModal = bootstrap.Modal.getInstance(document.getElementById('clearCancelledConfirmModal'));
    confirmModal.hide();
    
    try {
        const response = await fetch('/api/clear-cancelled-videos', {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            loadScheduledVideos();
            
            // Show success modal
            const messageEl = document.getElementById('clearCancelledMessage');
            if (data.cleared === 1) {
                messageEl.textContent = 'Cleared 1 cancelled video';
            } else {
                messageEl.textContent = `Cleared ${data.cleared} cancelled videos`;
            }
            
            const clearModal = new bootstrap.Modal(document.getElementById('clearCancelledModal'));
            clearModal.show();
        } else {
            alert('Failed to clear cancelled videos: ' + data.error);
        }
    } catch (error) {
        alert('Error clearing cancelled videos: ' + error.message);
    }
}

function showSchedulePromptPreview(scriptData) {
    try {
        // Use the same preview modal but change the button action
        showPromptPreview(scriptData);
        
        // Wait a bit for modal to be ready
        setTimeout(() => {
            // Change the button text and onclick
            const generateBtn = document.querySelector('#promptPreviewModal .modal-footer .btn-primary');
            if (generateBtn) {
                generateBtn.innerHTML = '<i class="bi bi-calendar-check"></i> Schedule Video';
                generateBtn.onclick = proceedWithScheduling;
            }
            
            // Add schedule info to the modal
            const modalBody = document.querySelector('#promptPreviewModal .modal-body');
            if (modalBody && pendingScheduleData) {
                const scheduleInfo = document.createElement('div');
                scheduleInfo.className = 'alert alert-info mb-3';
                scheduleInfo.innerHTML = `
                    <i class="bi bi-clock"></i> <strong>Scheduled for:</strong> 
                    ${new Date(pendingScheduleData.scheduledTime).toLocaleDateString()} at 
                    ${new Date(pendingScheduleData.scheduledTime).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                `;
                modalBody.insertBefore(scheduleInfo, modalBody.firstChild);
            }
        }, 100);
    } catch (error) {
        console.error('Error showing schedule preview:', error);
        alert('Error showing schedule preview: ' + error.message);
    }
}

async function proceedWithScheduling() {
    // Close modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('promptPreviewModal'));
    modal.hide();
    
    // Update script data with edited prompt
    pendingScheduleData.scriptData.visual_prompts = document.getElementById('previewPrompt').value;
    
    try {
        const response = await fetch('/api/schedule-video', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                topic: pendingScheduleData.topic,
                scheduledTime: pendingScheduleData.scheduledTime,
                duration: pendingScheduleData.duration,
                style: pendingScheduleData.style,
                scriptData: pendingScheduleData.scriptData,
                spreadsheetId: localStorage.getItem('spreadsheetId')
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Clear form
            document.getElementById('scheduleDate').value = '';
            document.getElementById('scheduleTime').value = '';
            document.getElementById('scheduleTopicInput').value = '';
            
            // Clear image selection
            document.getElementById('scheduleImageInput').value = '';
            document.getElementById('scheduleImagePreview').style.display = 'none';
            window.scheduleSelectedFiles = [];
            
            // Reload scheduled videos
            loadScheduledVideos();
            
            // Show success modal
            const scheduledTime = new Date(pendingScheduleData.scheduledTime);
            const timeDisplay = document.getElementById('scheduledTimeDisplay');
            timeDisplay.innerHTML = `
                ${scheduledTime.toLocaleDateString('en-US', { 
                    weekday: 'long', 
                    year: 'numeric', 
                    month: 'long', 
                    day: 'numeric' 
                })}<br>
                at ${scheduledTime.toLocaleTimeString('en-US', { 
                    hour: '2-digit', 
                    minute: '2-digit' 
                })}
            `;
            
            const successModal = new bootstrap.Modal(document.getElementById('scheduleSuccessModal'));
            successModal.show();
        } else {
            alert('Failed to schedule video: ' + data.error);
        }
    } catch (error) {
        alert('Error scheduling video: ' + error.message);
    }
}