document.addEventListener('DOMContentLoaded', () => {
    // Initialize marked.js with options
    marked.setOptions({
        highlight: function (code, lang) {
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
    const markdownEditor = document.getElementById('markdownEditor');
    const previewContent = document.getElementById('previewContent');
    const wordCount = document.getElementById('wordCount');
    const charCount = document.getElementById('charCount');
    const readingTime = document.getElementById('readingTime');
    const cursorPosition = document.getElementById('cursorPosition');
    const toolbar = document.getElementById('editorToolbar');
    const fullscreenBtn = document.getElementById('fullscreen');
    const copyMarkdownBtn = document.getElementById('copyMarkdown');
    const copyHtmlBtn = document.getElementById('copyHtml');
    const togglePreviewBtn = document.getElementById('togglePreview');
    const editorContainer = document.querySelector('.editor-container');

    // Initialize with sample content if empty
    if (!markdownEditor.value) {
        markdownEditor.value = '# Welcome to the Markdown Editor\n\nStart typing your content here...\n\n';
        updatePreview();
    }

    // Update preview with initial content
    updatePreview();

    // Function to update preview
    function updatePreview() {
        const markdown = markdownEditor.value;
        previewContent.innerHTML = marked.parse(markdown);
        updateCounts();

        // Apply syntax highlighting to code blocks
        previewContent.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
    }

    // Function to update word and character counts
    function updateCounts() {
        const text = markdownEditor.value;
        const words = text.trim().split(/\s+/).filter(word => word.length > 0).length;
        const chars = text.length;
        const minutes = Math.ceil(words / 200); // Assuming average reading speed of 200 words per minute

        wordCount.textContent = `Words: ${words}`;
        charCount.textContent = `Characters: ${chars}`;
        readingTime.textContent = `Reading Time: ${minutes} min`;
    }

    // Update cursor position
    function updateCursorPosition() {
        const pos = markdownEditor.selectionStart;
        const text = markdownEditor.value.substring(0, pos);
        const lines = text.split('\n');
        const line = lines.length;
        const column = lines[lines.length - 1].length + 1;
        cursorPosition.textContent = `Line: ${line}, Column: ${column}`;
    }

    // Live preview
    markdownEditor.addEventListener('input', () => {
        updatePreview();
        updateCursorPosition();
    });

    markdownEditor.addEventListener('keyup', updateCursorPosition);
    markdownEditor.addEventListener('click', updateCursorPosition);

    // Toolbar button functionality
    toolbar.addEventListener('click', (e) => {
        const button = e.target.closest('.toolbar-btn');
        if (!button) return;
        const action = button.dataset.action;
        const textarea = markdownEditor;
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const selectedText = textarea.value.substring(start, end);

        let replacement = '';

        switch (action) {
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
            case 'ul':
                replacement = selectedText.split('\n').map(line => `- ${line}`).join('\n');
                if (!selectedText) replacement = '- List item';
                break;
            case 'ol':
                replacement = selectedText.split('\n').map((line, i) => `${i + 1}. ${line}`).join('\n');
                if (!selectedText) replacement = '1. List item';
                break;
            case 'quote':
                replacement = selectedText.split('\n').map(line => `> ${line}`).join('\n');
                if (!selectedText) replacement = '> Quote';
                break;
            case 'table':
                replacement = `| Header 1 | Header 2 | Header 3 |\n|-----------|-----------|----------|\n| Cell 1    | Cell 2    | Cell 3    |`;
                break;
            case 'hr':
                replacement = '\n---\n';
                break;
            case 'undo':
                textarea.focus();
                return;
            case 'redo':
                document.execCommand('redo');
                return;
            default:
                return;
        }

        textarea.value =
            textarea.value.substring(0, start) +
            replacement +
            textarea.value.substring(end);

        // Set cursor position
        // const newCursorPos = start + replacement.length;
        // textarea.setSelectionRange(newCursorPos, newCursorPos);
        textarea.setSelectionRange(start, start + replacement.length);

        // Update preview
        updatePreview();
        updateCursorPosition();
        textarea.focus();
    });

    // Fullscreen toggle
    fullscreenBtn.addEventListener('click', () => {
        editorContainer.classList.toggle('fullscreen');
        fullscreenBtn.querySelector('i').classList.toggle('fa-expand');
        fullscreenBtn.querySelector('i').classList.toggle('fa-compress');
    });

    // Toggle preview
    togglePreviewBtn.addEventListener('click', () => {
        const previewPane = document.querySelector('.preview-pane');
        const editorPane = document.querySelector('.editor-pane');

        previewPane.classList.toggle('hidden');
        if (previewPane.classList.contains('hidden')) {
            editorPane.style.flex = '1';
            togglePreviewBtn.querySelector('i').classList.replace('fa-eye', 'fa-eye-slash');
        } else {
            editorPane.style.flex = '';
            togglePreviewBtn.querySelector('i').classList.replace('fa-eye-slash', 'fa-eye');
        }
    });

    // Copy functionality
    copyMarkdownBtn.addEventListener('click', async () => {
        try {
            await navigator.clipboard.writeText(markdownEditor.value);
            showNotification('Markdown copied to clipboard!');
        } catch (err) {
            showNotification('Failed to copy markdown', true);
        }
    });

    copyHtmlBtn.addEventListener('click', async () => {
        try {
            await navigator.clipboard.writeText(previewContent.innerHTML);
            showNotification('HTML copied to clipboard!');
        } catch (err) {
            showNotification('Failed to copy HTML', true);
        }
    });

    // Notification function
    function showNotification(message, isError = false) {
        const notification = document.createElement('div');
        notification.className = `notification ${isError ? 'error' : 'success'}`;
        notification.textContent = message;
        document.body.appendChild(notification);

        setTimeout(() => {
            notification.classList.add('show');
        }, 10);

        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 2000);
    }

    // Tab handling
    markdownEditor.addEventListener('keydown', (e) => {
        if (e.key === 'Tab') {
            e.preventDefault();
            const start = markdownEditor.selectionStart;
            const end = markdownEditor.selectionEnd;

            if (start === end) {
                // No selection, insert tab
                markdownEditor.value =
                    markdownEditor.value.substring(0, start) +
                    '    ' +
                    markdownEditor.value.substring(end);
                markdownEditor.selectionStart = markdownEditor.selectionEnd = start + 4;
            } else {
                // Selection exists, indent/unindent multiple lines
                const lines = markdownEditor.value.substring(start, end).split('\n');
                const indentedLines = e.shiftKey
                    ? lines.map(line => line.startsWith('    ') ? line.substring(4) : line)
                    : lines.map(line => '    ' + line);

                markdownEditor.value =
                    markdownEditor.value.substring(0, start) +
                    indentedLines.join('\n') +
                    markdownEditor.value.substring(end);

                markdownEditor.selectionStart = start;
                markdownEditor.selectionEnd = start + indentedLines.join('\n').length;
            }

            updatePreview();
            updateCursorPosition();
        }
    });

    // Keyboard shortcuts
    markdownEditor.addEventListener('keydown', (e) => {
        if (e.ctrlKey || e.metaKey) {
            switch (e.key.toLowerCase()) {
                case 'b':
                    e.preventDefault();
                    document.querySelector('[data-action="bold"]').click();
                    break;
                case 'i':
                    e.preventDefault();
                    document.querySelector('[data-action="italic"]').click();
                    break;
                case 'k':
                    e.preventDefault();
                    document.querySelector('[data-action="link"]').click();
                    break;
            }
        }
    });

    // Auto-save to localStorage
    const AUTO_SAVE_INTERVAL = 5000; // 5 seconds
    const AUTO_SAVE_KEY = 'markdown-editor-content';

    function saveToLocalStorage() {
        localStorage.setItem(AUTO_SAVE_KEY, markdownEditor.value);
    }

    // Load content from localStorage
    const savedContent = localStorage.getItem(AUTO_SAVE_KEY);
    if (savedContent) {
        markdownEditor.value = savedContent;
        updatePreview();
    }

    // Set up auto-save interval
    setInterval(saveToLocalStorage, AUTO_SAVE_INTERVAL);

    // Handle paste events for images
    markdownEditor.addEventListener('paste', async (e) => {
        const items = (e.clipboardData || e.originalEvent.clipboardData).items;

        for (let item of items) {
            if (item.type.indexOf('image') === 0) {
                e.preventDefault();
                const file = item.getAsFile();
                const reader = new FileReader();

                reader.onload = function (event) {
                    const imageUrl = event.target.result;
                    const imageMarkdown = `![Pasted Image](${imageUrl})`;

                    const start = markdownEditor.selectionStart;
                    markdownEditor.value =
                        markdownEditor.value.substring(0, start) +
                        imageMarkdown +
                        markdownEditor.value.substring(start);

                    updatePreview();
                };

                reader.readAsDataURL(file);
            }
        }
    });
});
