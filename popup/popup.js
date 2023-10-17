var jsMapFiles = [];
var BACKEND_URL = 'https://7vvgncd5j2p4p3k42kcp5nqd4y0doxgp.lambda-url.us-east-1.on.aws'
async function getGeneratedCode() {
    document.getElementById('loading').style.display = 'block';
    const data = {
        jsLinks: jsMapFiles
    };

    try {
        const res = await fetch(BACKEND_URL, {
            method: 'POST',
            body: JSON.stringify(data)
        });

        if (res.status !== 200) {
            throw new Error('Cannot fetch generated code');
        }

        const blob = await res.blob();

        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'source.zip';
        a.style.display = 'none';

        document.body.appendChild(a);
        a.click();

        // Clean up after the download
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

    } catch (error) {
        console.error('Error while fetching or downloading code:', error);
    }
    document.getElementById('loading').style.display = 'none';
}

document.getElementById('generate-code').addEventListener('click', getGeneratedCode);


async function getCurrentTab() {
    let queryOptions = { active: true, lastFocusedWindow: true };
    // `tab` will either be a `tabs.Tab` instance or `undefined`.
    let [tab] = await chrome.tabs.query(queryOptions);
    return tab;
}

async function getTabUrl() {
    let tab = await getCurrentTab();
    return tab && tab.url;
}

const isValidDomain = (domain) => {
    return domain && domain.includes('http');
}

async function getPageJs() {
    const url = await getTabUrl();
    const domain = new URL(url).origin;
    if (!domain || !isValidDomain(domain)) {
        throw new Error('Cannot get domain');
    }
    const res = await fetch(domain);
    if (res.status !== 200) {
        throw new Error('Cannot fetch page');
    }
    const jslinks = [];
    const text = await res.text();
    const js = text.match(/<script.*?>([\s\S]*?)<\/script>/g);
    js.forEach((script) => {
        const src = script.match(/src="(.*?)"/);
        // make sure the links are not external and not empty
        if (src && src[1] && !src[1].includes('http')) {
            jslinks.push(domain + src[1]);
        }
    });
    return jslinks;
}

async function checkJsMapFiles() {
    const jslinks = await getPageJs();
    for (let i = 0; i < jslinks.length; i++) {
        const jslink = jslinks[i];
        const jsMapFile = jslink + '.map';
        const res = await fetch(jsMapFile);
        if (res.status === 200) {
            jsMapFiles.push(jsMapFile);
        }
    }
    return jsMapFiles;
}

checkJsMapFiles().then((jsMapFiles) => {
    document.getElementById('loading').style.display = 'none';
    if (jsMapFiles.length > 0) {
        console.log('Found js map files');
        document.getElementById('result').innerHTML = 'I might be able to help you';
        document.getElementById('generate-code').style.display = 'block';
    } else {
        console.log('No js map files found');
        document.getElementById('result').innerHTML = 'I cannot help you. I cannot generate source code from thin air. Try another site.';
        document.getElementById('generate-code').style.display = 'none';
    }
}).catch((err) => {
    console.log(err);
    document.getElementById('loading').style.display = 'none';
    document.getElementById('result').innerHTML = 'I cannot help you. I cannot generate source code from thin air. Try another site.';
    document.getElementById('generate-code').style.display = 'none';
})

// Path: popup/popup.js