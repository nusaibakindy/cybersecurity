const express = require('express');
const session = require('express-session');
const bodyParser = require('body-parser');
const { Sequelize, DataTypes } = require('sequelize');
const bcrypt = require('bcrypt');
const multer = require('multer');
const path = require('path');
const fs = require('fs');

const app = express();
app.use(bodyParser.urlencoded({ extended: true }));
app.use(session({
    secret: 'replace_with_your_secret_key',
    resave: false,
    saveUninitialized: false
}));

// Serve static files from the "public" folder
app.use(express.static(path.join(__dirname, 'public')));

// Instead of diskStorage, we use memoryStorage so that file data is available in req.file.buffer
const storage = multer.memoryStorage();
const fileFilter = (req, file, cb) => {
    if (path.extname(file.originalname).toLowerCase() === '.pdf') {
        cb(null, true);
    } else {
        cb(new Error('Only PDF files are allowed'), false);
    }
};
const upload = multer({ storage: storage, fileFilter: fileFilter });

// Initialize Sequelize with SQLite
const sequelize = new Sequelize({
    dialect: 'sqlite',
    storage: 'secureportal.db',
    logging: false
});gslkfdjghghhg

// Define Models
const User = sequelize.define('User', {
    username: {
        type: DataTypes.STRING,
        unique: true,
        allowNull: false
    },
    passwordHash: {
        type: DataTypes.STRING,
        allowNull: false
    },
    role: {
        type: DataTypes.STRING,
        allowNull: false  // 'user' or 'admin'
    }
});

const Document = sequelize.define('Document', {
    filename: {
        type: DataTypes.STRING,
        allowNull: false
    },
    uploaderId: {
        type: DataTypes.INTEGER,
        allowNull: false
    },
    fileData: {
        type: DataTypes.BLOB('long'),
        allowNull: false
    }
});

// Helper function: Enforce strong password policy
function validPassword(password) {
    if (password.length < 8) return false;
    if (!/[A-Z]/.test(password)) return false;
    if (!/[a-z]/.test(password)) return false;
    if (!/[\W_]/.test(password)) return false;
    return true;
}

// Middleware to fetch logged-in user
async function currentUser(req, res, next) {
    if (req.session.userId) {
        try {
            req.user = await User.findByPk(req.session.userId);
        } catch (error) {
            req.user = null;
        }
    }
    next();
}
app.use(currentUser);

// Generic error handler middleware
app.use((err, req, res, next) => {
    console.error(err);
    res.status(500).send(`
        <h2>An error occurred</h2>
        <p>Please try again later.</p>
        <p><a href="/">Home</a></p>
    `);
});

// Routes

// Home page
app.get('/', (req, res) => {
    if (req.user) {
        res.send(`
            <h2>Welcome ${req.user.username} (${req.user.role})</h2>
            <p><a href="/upload.html">Upload Document</a></p>
            <p><a href="/documents.html">View Documents</a></p>
            <p><a href="/logout">Logout</a></p>
        `);
    } else {
        res.send(`
            <h2>SecurePortal</h2>
            <p><a href="/login.html">Login</a></p>
            <p><a href="/register.html">Register</a></p>
        `);
    }
});

// Registration Route
app.get('/register', (req, res) => {
    res.redirect('/register.html');
});
app.post('/register', async (req, res) => {
    const { username, password, role } = req.body;
    if (!username || !password) {
        return res.redirect('/register.html');
    }
    if (!validPassword(password)) {
        return res.send('<p>Weak password. Must be at least 8 chars long with one uppercase, one lowercase, and one special character.</p><p><a href="/register.html">Try again</a></p>');
    }
    const existingUser = await User.findOne({ where: { username } });
    if (existingUser) {
        return res.send('<p>Username already exists.</p><p><a href="/register.html">Try again</a></p>');
    }
    const hash = await bcrypt.hash(password, 10);
    await User.create({ username, passwordHash: hash, role });
    res.send('<p>Registration successful. <a href="/login.html">Login</a></p>');
});

// Login Route
app.get('/login', (req, res) => {
    res.redirect('/login.html');
});
app.post('/login', async (req, res) => {
    const { username, password } = req.body;
    const user = await User.findOne({ where: { username } });
    if (user && await bcrypt.compare(password, user.passwordHash)) {
        req.session.userId = user.id;
        return res.redirect('/');
    }
    res.send('<p>Invalid credentials.</p><p><a href="/login.html">Try again</a></p>');
});

// Logout Route
app.get('/logout', (req, res) => {
    req.session.destroy();
    res.redirect('/');
});

// Upload Route (PDF only)
app.get('/upload', (req, res) => {
    if (!req.user) return res.redirect('/login.html');
    res.redirect('/upload.html');
});
app.post('/upload', upload.single('file'), async (req, res) => {
    if (!req.user) return res.redirect('/login.html');
    if (!req.file) return res.send('<p>No file uploaded.</p><p><a href="/upload.html">Try again</a></p>');
    // Save the file data in the database instead of the file system
    await Document.create({ 
        filename: req.file.originalname,
        uploaderId: req.user.id,
        fileData: req.file.buffer 
    });
    res.send('<p>File successfully uploaded.</p><p><a href="/documents.html">View Documents</a></p>');
});

// Documents Viewing Route
app.get('/documents', async (req, res) => {
    if (!req.user) return res.redirect('/login.html');
    let documents;
    if (req.user.role === 'admin') {
        documents = await Document.findAll();
    } else {
        documents = await Document.findAll({ where: { uploaderId: req.user.id } });
    }
    let listItems = '';
    documents.forEach(doc => {
        listItems += `<li>${doc.filename} - <a href="/uploads/${doc.filename}">Download</a></li>`;
    });
    if (!listItems) listItems = '<li>No documents found.</li>';
    res.send(`
        <h2>Uploaded Documents</h2>
        <ul>${listItems}</ul>
        <p><a href="/">Home</a></p>
    `);
});

// Download Route - Retrieve file data from the database
app.get('/uploads/:filename', async (req, res) => {
    if (!req.user) return res.redirect('/login.html');
    const document = await Document.findOne({ where: { filename: req.params.filename } });
    if (!document) {
        return res.send('<p>File not found.</p><p><a href="/documents.html">Back</a></p>');
    }
    res.set('Content-Type', 'application/pdf');
    res.set('Content-Disposition', `attachment; filename="${document.filename}"`);
    res.send(document.fileData);
});

// Start the server and sync database
sequelize.sync().then(() => {
    app.listen(3000, () => {
        console.log('SecurePortal running on http://localhost:3000');
    });
});