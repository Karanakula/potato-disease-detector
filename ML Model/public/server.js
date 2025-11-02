// ✅ ES6-style imports
import express from "express";
import multer from "multer";
import axios from "axios";
import fs from "fs";
import FormData from "form-data";
import path from "path";
import mongoose from "mongoose";
import bodyParser from "body-parser";
import cookieSession from "cookie-session";
import nodemailer from "nodemailer";
import { fileURLToPath } from "url";
import { dirname } from "path";
import dotenv from "dotenv";

// Load environment variables
dotenv.config();

// ✅ Setup for __dirname in ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// ✅ Initialize express app
const app = express();
const port = process.env.PORT || 3000;

// ✅ MongoDB connection
const MONGODB_URI = process.env.MONGODB_URI || "mongodb://127.0.0.1:27017/studentDB";

console.log("🔌 Connecting to MongoDB...");
mongoose.connect(MONGODB_URI)
  .then(() => {
    console.log("✅ MongoDB Connected");
    if (MONGODB_URI.includes('mongodb+srv')) {
      console.log("☁️  Using MongoDB Atlas (Cloud)");
    } else {
      console.log("💻 Using Local MongoDB");
    }
  })
  .catch((err) => console.error("❌ MongoDB Connection Error:", err));

// ✅ Schemas
const userSchema = new mongoose.Schema({
  email: String,
  password: String,
});
const User = mongoose.model("User", userSchema);

const predictionSchema = new mongoose.Schema({
  userEmail: String,
  prediction: String,
  confidence: Number,
  date: { type: Date, default: Date.now },
});
const Prediction = mongoose.model("Prediction", predictionSchema);

// ✅ Middleware
app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "views"));
app.use(express.static(__dirname));
app.use(bodyParser.urlencoded({ extended: true }));

app.use(cookieSession({
  name: "session",
  keys: [process.env.SESSION_SECRET || "your_secret_key"],
  maxAge: 24 * 60 * 60 * 1000,
}));

// ✅ Multer for file uploads
const upload = multer({ dest: "uploads/" });

// ✅ Nodemailer transporter using App Password
const transporter = nodemailer.createTransport({
  service: "gmail",
  auth: {
    user: "akula.work01@gmail.com",
    pass: "staqdmebfwvvkarf", // App password without spaces
  },
});

// ✅ Routes

app.get("/", (req, res) => res.render("home", { session: req.session }));
app.get("/home", (req, res) => res.render("home", { session: req.session }));
app.get("/about", (req, res) => res.render("about", { session: req.session }));

app.get("/signup", (req, res) => res.render("signup", { session: req.session }));
app.get("/login", (req, res) => res.render("login", { session: req.session }));

app.post("/register", async (req, res) => {
  const email = req.body.username.toLowerCase();
  const password = req.body.password;

  const existingUser = await User.findOne({ email });
  if (existingUser) return res.send("Email already registered");

  await new User({ email, password }).save();
  res.redirect("/login");
});

app.post("/login", async (req, res) => {
  const email = req.body.username.toLowerCase();
  const password = req.body.password;

  const user = await User.findOne({ email });
  if (!user) return res.status(400).send("User not found");
  if (password !== user.password) return res.status(401).send("Incorrect password");

  req.session.email = email;
  res.redirect("/predict");
});

app.get("/logout", (req, res) => {
  req.session = null;
  res.redirect("/login");
});

app.post("/logout", (req, res) => {
  req.session = null;
  res.redirect("/login");
});

app.get("/predict", (req, res) => {
  if (!req.session.email) return res.redirect("/login");
  res.render("index", { result: null, session: req.session });
});

app.post("/predict", upload.single("image"), async (req, res) => {
  if (!req.session.email) return res.redirect("/login");
  if (!req.file) {
    return res.render("index", {
      result: { error: "No file uploaded" },
      session: req.session,
    });
  }

  try {
    const filePath = req.file.path;
    const formData = new FormData();
    formData.append("image", fs.createReadStream(filePath));

    // Use environment variable for Flask API URL
    const FLASK_API_URL = process.env.FLASK_API_URL || "http://127.0.0.1:5000";
    const response = await axios.post(`${FLASK_API_URL}/predict`, formData, {
      headers: formData.getHeaders(),
    });

    fs.unlinkSync(filePath);

    const { prediction, confidence } = response.data;

    await Prediction.create({
      userEmail: req.session.email,
      prediction,
      confidence,
    });

    res.render("index", {
      result: { prediction, confidence },
      session: req.session,
    });

  } catch (err) {
    console.error("Prediction Error:", err);
    res.render("index", {
      result: { error: "Prediction failed. Please try again." },
      session: req.session,
    });
  }
});

app.get("/profile", async (req, res) => {
  if (!req.session.email) return res.redirect("/login");

  const predictions = await Prediction.find({ userEmail: req.session.email }).sort({ date: -1 });

  const diseaseCounts = {};
  for (let p of predictions) {
    diseaseCounts[p.prediction] = (diseaseCounts[p.prediction] || 0) + 1;
  }

  const chartData = {
    labels: Object.keys(diseaseCounts),
    counts: Object.values(diseaseCounts),
  };

  const total = predictions.length;
  const healthy = predictions.filter(p => p.prediction.toLowerCase().includes("healthy")).length;
  const diseased = total - healthy;

  res.render("profile", {
    predictions,
    chartData,
    total,
    healthy,
    diseased,
    session: req.session,
  });
});

app.get("/contact", (req, res) => {
  res.render("contact", { session: req.session, messageSent: false });
});

app.post("/contact", (req, res) => {
  const { name, email, message } = req.body;

  const mailOptions = {
    from: email,
    to: "akula.work01@gmail.com",
    subject: `Contact Form Submission from ${name}`,
    text: message,
  };

  transporter.sendMail(mailOptions, (err, info) => {
    if (err) {
      console.error("❌ Email send failed:", err);
      return res.status(500).send("Message failed to send");
    }
    console.log("✅ Email sent:", info.response);
    res.render("contact", { session: req.session, messageSent: true });
  });
});

// ✅ Start Server
app.listen(port, () => {
  console.log(`🚀 Server running at http://127.0.0.1:${port}`);
});
