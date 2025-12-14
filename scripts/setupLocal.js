const fs = require('fs');
const path = require('path');

const projectRoot = process.cwd();
const directories = [
    'data/mailserver/cur',
    'data/mailserver/new',
    'data/mailserver/home',
    'data/tmp/feedback',
    'data/tmp/reports',
    'data/tmp/screenshots'
];

directories.forEach((dir) => {
    const target = path.join(projectRoot, dir);
    fs.mkdirSync(target, { recursive: true });
});

console.log('Local data directories are ready.');
