// backend/server.js
import express from "express";
import dotenv from "dotenv";
import cors from "cors";
import mongoose from "mongoose";
import cookieParser from "cookie-parser";
import songRoutes from "./routes/songRoutes.js";
import playlistRoutes from "./routes/playlistRoutes.js";
import userRoutes from "./routes/userRoutes.js";
import passport from "passport";
import session from "express-session";
import "./config/passport.js";
import jwt from "jsonwebtoken";
import bodyParser from "body-parser";
import User from "./models/User.js";
import Song from "./models/Song.js";
import Playlist from "./models/Playlist.js";
import path from "path";
import fs from "fs";

// Load environment variables
dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors({ origin: process.env.CLIENT_URL, credentials: true }));
app.use(express.json());
app.use(bodyParser.urlencoded({ extended: true }));
app.use(cookieParser());
app.use(session({
  secret: process.env.SESSION_SECRET,
  resave: false,
  saveUninitialized: false,
}));
app.use(passport.initialize());
app.use(passport.session());

// Playback Controls
let playbackState = {
  isPlaying: false,
  currentSong: null,
  queue: [],
  repeatMode: false,
};

app.post("/api/playback/play", (req, res) => {
  playbackState.isPlaying = true;
  playbackState.currentSong = req.body.songId;
  res.json({ message: "Playback started", playbackState });
});

app.post("/api/playback/pause", (req, res) => {
  playbackState.isPlaying = false;
  res.json({ message: "Playback paused", playbackState });
});

app.post("/api/playback/skip", (req, res) => {
  playbackState.currentSong = playbackState.queue.shift() || null;
  res.json({ message: "Song skipped", playbackState });
});

app.post("/api/playback/shuffle", (req, res) => {
  playbackState.queue.sort(() => Math.random() - 0.5);
  res.json({ message: "Shuffle activated", playbackState });
});

app.post("/api/playback/repeat", (req, res) => {
  playbackState.repeatMode = !playbackState.repeatMode;
  res.json({ message: "Repeat mode toggled", playbackState });
});

app.post("/api/playback/queue", (req, res) => {
  playbackState.queue.push(req.body.songId);
  res.json({ message: "Song added to queue", playbackState });
});

// Song Routes
app.get("/api/songs", async (req, res) => {
  try {
    const songs = await Song.find();
    res.json(songs);
  } catch (error) {
    res.status(500).json({ message: "Server error" });
  }
});

// Music Metadata Route
app.get("/api/songs/metadata/:id", async (req, res) => {
  try {
    const song = await Song.findById(req.params.id);
    if (!song) return res.status(404).json({ message: "Song not found" });
    res.json({
      title: song.title,
      artist: song.artist,
      album: song.album,
      duration: song.duration,
      coverArt: song.coverArt,
    });
  } catch (error) {
    res.status(500).json({ message: "Server error" });
  }
});

// Music Streaming Route
app.get("/api/songs/stream/:id", async (req, res) => {
  try {
    const song = await Song.findById(req.params.id);
    if (!song) return res.status(404).json({ message: "Song not found" });
    
    const filePath = path.join(__dirname, "music", song.fileName);
    if (!fs.existsSync(filePath)) return res.status(404).json({ message: "File not found" });
    
    res.setHeader("Content-Type", "audio/mpeg");
    fs.createReadStream(filePath).pipe(res);
  } catch (error) {
    res.status(500).json({ message: "Server error" });
  }
});

// Playlist Routes
app.post("/api/playlists", async (req, res) => {
  try {
    const { name, songs } = req.body;
    const newPlaylist = new Playlist({ name, songs });
    await newPlaylist.save();
    res.json(newPlaylist);
  } catch (error) {
    res.status(500).json({ message: "Server error" });
  }
});

app.put("/api/playlists/:id", async (req, res) => {
  try {
    const updatedPlaylist = await Playlist.findByIdAndUpdate(req.params.id, req.body, { new: true });
    if (!updatedPlaylist) return res.status(404).json({ message: "Playlist not found" });
    res.json(updatedPlaylist);
  } catch (error) {
    res.status(500).json({ message: "Server error" });
  }
});

app.delete("/api/playlists/:id", async (req, res) => {
  try {
    const deletedPlaylist = await Playlist.findByIdAndDelete(req.params.id);
    if (!deletedPlaylist) return res.status(404).json({ message: "Playlist not found" });
    res.json({ message: "Playlist deleted successfully" });
  } catch (error) {
    res.status(500).json({ message: "Server error" });
  }
});

// Routes
app.use("/api/users", userRoutes);
app.use("/api/songs", songRoutes);
app.use("/api/playlists", playlistRoutes);

// Database Connection
mongoose.connect(process.env.MONGO_URI, {
  useNewUrlParser: true,
  useUnifiedTopology: true,
})
.then(() => console.log("MongoDB Connected"))
.catch(err => console.error("MongoDB Connection Error:", err));

// Start Server
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
