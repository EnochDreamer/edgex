document.addEventListener('DOMContentLoaded', () => {
    // Initialize marked.js with options
    marked.setOptions({
        highlight: function(code, lang) {
            if (hljs.getLanguage(lang)) {
                return hljs.highlight(code, { language: lang }).value;
            }
            return code;
        },
        langPrefix: 'hljs language-',
        gfm: true,
        breaks: true
    });

    // DOM Elements
    const markdownInput = document.querySelector('.markdown-input');
    const preview = document.querySelector('.markdown-preview');
    const wordCount = document.querySelector('.word-count');
    const charCount = document.querySelector('.char-count');
    const toolbar = document.querySelector('.editor-toolbar');
    const fullscreenBtn = document.querySelector('.fullscreen-btn');
    const container = document.querySelector('.editor-container');

    // Initialize with sample content if empty
    if (!markdownInput.value) {
        markdownInput.value = '# Welcome to the Markdown Editor\n\nStart typing your content here...\n\n';
        updatePreview();
    }

    // Update preview with initial content
    updatePreview();

    // Function to update preview
    function updatePreview() {
        const markdown = markdownInput.value;
        preview.innerHTML = marked(markdown);
        updateCounts();
        
        // Apply syntax highlighting to code blocks
        preview.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
    }

    // Function to update word and character counts
    function updateCounts() {
        const text = markdownInput.value;
        const words = text.trim().split(/\s+/).filter(word => word.length > 0).length;
        const chars = text.length;
        
        wordCount.textContent = `Words: ${words}`;
        charCount.textContent = `Characters: ${chars}`;
    }

    // Live preview
    markdownInput.addEventListener('input', updatePreview);

    // Toolbar button functionality
    toolbar.addEventListener('click', (e) => {
        if (!e.target.matches('.toolbar-btn')) return;
        
        const action = e.target.dataset.action;
        const textarea = markdownInput;
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const selectedText = textarea.value.substring(start, end);
        
        let replacement = '';
        
        switch(action) {
            case 'bold':
                replacement = `**${selectedText || 'bold text'}**`;
                break;
            case 'italic':
                replacement = `*${selectedText || 'italic text'}*`;
                break;
            case 'heading':
                replacement = `# ${selectedText || 'Heading'}`;
                break;
            case 'link':
                replacement = `[${selectedText || 'link text'}](url)`;
                break;
            case 'image':
                replacement = `![${selectedText || 'alt text'}](image-url)`;
                break;
            case 'code':
                replacement = selectedText.includes('\n')
                    ? `\`\`\`\n${selectedText || 'code'}\n\`\`\``
                    : `\`${selectedText || 'code'}\``;
                break;
            case 'list':
                replacement = `\n- ${selectedText || 'List item'}`;
                break;
            case 'quote':
                replacement = `> ${selectedText || 'Quote'}`;
                break;
            default:
                return;
        }
        
        textarea.value = 
            textarea.value.substring(0, start) +
            replacement +
            textarea.value.substring(end);
            
        // Set cursor position
        const newCursorPos = start + replacement.length;
        textarea.setSelectionRange(newCursorPos, newCursorPos);
        
        // Update preview
        updatePreview();
        textarea.focus();
    });

    // Fullscreen toggle
    fullscreenBtn.addEventListener('click', () => {
        container.classList.toggle('fullscreen');
        fullscreenBtn.querySelector('i').classList.toggle('fa-expand');
        fullscreenBtn.querySelector('i').classList.toggle('fa-compress');
    });

    // Tab handling
    markdownInput.addEventListener('keydown', (e) => {
        if (e.key === 'Tab') {
            e.preventDefault();
            const start = markdownInput.selectionStart;
            const end = markdownInput.selectionEnd;
            
            markdownInput.value = 
                markdownInput.value.substring(0, start) +
                '    ' +
                markdownInput.value.substring(end);
                
            markdownInput.setSelectionRange(start + 4, start + 4);
            updatePreview();
        }
    });

    // Auto-save to localStorage
    const autoSave = () => {
        localStorage.setItem('markdown-content', markdownInput.value);
    };

    // Load content from localStorage
    const savedContent = localStorage.getItem('markdown-content');
    if (savedContent) {
        markdownInput.value = savedContent;
        updatePreview();
    }

    // Set up auto-save interval
    setInterval(autoSave, 5000);

    // Handle paste events for images
    markdownInput.addEventListener('paste', async (e) => {
        const items = (e.clipboardData || e.originalEvent.clipboardData).items;
        
        for (let item of items) {
            if (item.type.indexOf('image') === 0) {
                e.preventDefault();
                const file = item.getAsFile();
                const reader = new FileReader();
                
                reader.onload = function(event) {
                    const imageUrl = event.target.result;
                    const imageMarkdown = `![Pasted Image](${imageUrl})`;
                    
                    const start = markdownInput.selectionStart;
                    markdownInput.value = 
                        markdownInput.value.substring(0, start) +
                        imageMarkdown +
                        markdownInput.value.substring(start);
                        
                    updatePreview();
                };
                
                reader.readAsDataURL(file);
            }
        }
    });
});
