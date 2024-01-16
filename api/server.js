/**
 * Creates a server with the following specifications:
 * 1. Imports express and dotenv node modules.
 * 2. Creates the server with express and names it app.
 * 3. Uses port 8080 as the default port.
 * 4. Enables body parser to accept JSON data.
 * 5. States which port the server is listening to and logs it to the console.
 */

const express = require('express');
const dotenv = require('dotenv');

const app = express();

dotenv.config();


app.use(express.json());


const PORT = process.env.PORT || 8080;

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
}
);

// Path: api/routes/notes.js



/**
 * 
 * @param {object} req
 *  