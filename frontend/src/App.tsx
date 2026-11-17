import { FormEvent, useEffect, useRef, useState } from "react";

type Track = {
  track_id: string;
  track_name: string;
  artist: string;
  album?: string | null;
  language?: string | null;
  genre_tags: string[];
  mood_tags: string[];
  relevance_score: number;
  explanation: string;
  listening_url?: string | null;
  preview_url?: string | null;
  availability_status: string;
};

type Memory = {
  id: number;
  memory_title: string;
  summary: string;
  story: string;
  emotions: string[];
  themes: string[];
  recommendations: Array<{ track_name: string; artist: string }>;
  created_at: string;
};

type Preferences = {
  preferred_languages: string[];
  preferred_genres: string[];
  disliked_genres: string[];
  explicit_content: "allow" | "avoid" | "unknown";
  diversity: number;
};

type Soundtrack = {
  memory_analysis: {
    memory_title: string;
    summary: string;
    primary_emotions: string[];
    secondary_emotions: string[];
    themes: string[];
    language?: string | null;
    atmosphere: string;
  };
  recommendations: Track[];
  overall_explanation: string;
};

const examples = [
  "The train ride home after my first year away felt like a quiet return to myself.",
  "My cousins and I played outside until sunset while my grandmother made dinner.",
  "I opened my first job offer and called my parents before telling anyone else.",
];

async function createSoundtrack(memory: string): Promise<Soundtrack> {
  const response = await fetch("/api/soundtracks", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ memory }),
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail ?? "The soundtrack could not be created.");
  }
  return response.json() as Promise<Soundtrack>;
}

async function refineSoundtrack(memory: string, result: Soundtrack, instruction: string): Promise<Soundtrack> {
  const response = await fetch("/api/soundtracks/refine", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ memory, result, instruction }),
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.detail ?? "The soundtrack could not be refined.");
  return payload as Soundtrack;
}

async function sendFeedback(trackId: string, feedbackType: string): Promise<void> {
  await fetch("/api/feedback", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ track_id: trackId, feedback_type: feedbackType }),
  });
}

async function loadMemories(): Promise<Memory[]> {
  const response = await fetch("/api/memories");
  if (!response.ok) throw new Error("Saved memories could not be loaded.");
  return response.json() as Promise<Memory[]>;
}

async function loadPreferences(): Promise<Preferences> {
  const response = await fetch("/api/preferences");
  if (!response.ok) throw new Error("Preferences could not be loaded.");
  return response.json() as Promise<Preferences>;
}

export default function App() {
  const [memory, setMemory] = useState("");
  const [soundtrack, setSoundtrack] = useState<Soundtrack | null>(null);
  const [refinement, setRefinement] = useState("");
  const [refining, setRefining] = useState(false);
  const [view, setView] = useState<"create" | "vault" | "preferences">("create");
  const [memories, setMemories] = useState<Memory[]>([]);
  const [preferences, setPreferences] = useState<Preferences | null>(null);
  const [pageLoading, setPageLoading] = useState(false);
  const [pageError, setPageError] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [feedback, setFeedback] = useState<Record<string, string>>({});
  const [recording, setRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [voiceError, setVoiceError] = useState("");
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  useEffect(() => () => {
    recorderRef.current?.stream.getTracks().forEach((track) => track.stop());
  }, []);

  const startRecording = async () => {
    setVoiceError("");
    if (!navigator.mediaDevices?.getUserMedia) {
      setVoiceError("Microphone capture is not supported in this browser.");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };
      recorder.onstop = () => {
        setAudioBlob(new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" }));
        stream.getTracks().forEach((track) => track.stop());
      };
      recorderRef.current = recorder;
      recorder.start();
      setRecording(true);
    } catch {
      setVoiceError("Microphone permission was not granted.");
    }
  };

  const stopRecording = () => {
    recorderRef.current?.stop();
    setRecording(false);
  };

  const transcribeRecording = async () => {
    if (!audioBlob) return;
    const formData = new FormData();
    formData.append("file", audioBlob, "memory.webm");
    setVoiceError("");
    try {
      const response = await fetch("/api/speech/transcribe", { method: "POST", body: formData });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail ?? "The recording could not be transcribed.");
      setMemory(payload.transcription ?? "");
      setAudioBlob(null);
    } catch (requestError) {
      setVoiceError(requestError instanceof Error ? requestError.message : "The recording could not be transcribed.");
    }
  };

  const openVault = async () => {
    setView("vault");
    setPageLoading(true);
    setPageError("");
    try {
      setMemories(await loadMemories());
    } catch (requestError) {
      setPageError(requestError instanceof Error ? requestError.message : "Saved memories could not be loaded.");
    } finally {
      setPageLoading(false);
    }
  };

  const openPreferences = async () => {
    setView("preferences");
    setPageLoading(true);
    setPageError("");
    try {
      setPreferences(await loadPreferences());
    } catch (requestError) {
      setPageError(requestError instanceof Error ? requestError.message : "Preferences could not be loaded.");
    } finally {
      setPageLoading(false);
    }
  };

  const savePreferences = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!preferences) return;
    setPageLoading(true);
    setPageError("");
    try {
      const response = await fetch("/api/preferences", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(preferences),
      });
      if (!response.ok) throw new Error("Preferences could not be saved.");
    } catch (requestError) {
      setPageError(requestError instanceof Error ? requestError.message : "Preferences could not be saved.");
    } finally {
      setPageLoading(false);
    }
  };

  const deleteMemory = async (id: number) => {
    const response = await fetch(`/api/memories/${id}`, { method: "DELETE" });
    if (response.ok) setMemories(memories.filter((memoryItem) => memoryItem.id !== id));
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (memory.trim().length < 10) {
      setError("Write at least a sentence so the feeling has room to emerge.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      setSoundtrack(await createSoundtrack(memory.trim()));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  const chooseExample = (example: string) => {
    setMemory(example);
    setSoundtrack(null);
    setError("");
  };

  const submitRefinement = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!soundtrack || !refinement.trim()) return;
    setRefining(true);
    setError("");
    try {
      setSoundtrack(await refineSoundtrack(memory, soundtrack, refinement.trim()));
      setRefinement("");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "The soundtrack could not be refined.");
    } finally {
      setRefining(false);
    }
  };

  return (
    <main className="shell">
      <nav className="nav" aria-label="Main navigation">
        <button className="brand brand-button" type="button" onClick={() => setView("create")} aria-label="Create a soundtrack">
          <span className="brand-mark">◒</span>
          <span>The Soundtrack<br /><em>of Your Life</em></span>
        </button>
        <div className="nav-actions">
          <button type="button" className={view === "create" ? "active" : ""} onClick={() => setView("create")}>Create</button>
          <button type="button" className={view === "vault" ? "active" : ""} onClick={() => void openVault()}>Memory vault</button>
          <button type="button" className={view === "preferences" ? "active" : ""} onClick={() => void openPreferences()}>Preferences</button>
        </div>
        <span className="nav-note">Local-first · private by design</span>
      </nav>

      {view === "create" ? <>
      <section className="hero" aria-labelledby="hero-title">
        <div className="hero-copy">
          <p className="eyebrow">A musical memory studio</p>
          <h1 id="hero-title">Your life has a soundtrack.<br /><i>Let’s find it.</i></h1>
          <p className="hero-lede">Describe a moment that stayed with you. We’ll listen for the feeling beneath the words and shape it into a thoughtful, personal soundtrack.</p>
        </div>
        <div className="orbit" aria-hidden="true"><span>memory</span><span>feeling</span><span>sound</span></div>
      </section>

      <section className="composer" aria-labelledby="composer-title">
        <div className="section-heading">
          <span className="section-index">01</span>
          <div><h2 id="composer-title">Begin with a memory</h2><p>There is no right length or perfect way to tell it.</p></div>
        </div>
        <form onSubmit={submit}>
          <label className="sr-only" htmlFor="memory">Your memory</label>
          <div className="voice-tools" aria-live="polite">
            <button className={`voice-button ${recording ? "recording" : ""}`} type="button" onClick={recording ? stopRecording : startRecording}>
              <span className="voice-dot" aria-hidden="true" /> {recording ? "Stop recording" : "Record a memory"}
            </button>
            {audioBlob && <button className="transcribe-button" type="button" onClick={() => void transcribeRecording()}>Transcribe recording</button>}
            {recording && <span className="recording-status">Recording — your voice is not transcribed live</span>}
          </div>
          {voiceError && <p className="error" role="alert">{voiceError}</p>}
          <textarea id="memory" value={memory} onChange={(event) => setMemory(event.target.value)} placeholder="I remember..." maxLength={5000} />
          <div className="composer-footer">
            <span className="character-count">{memory.length.toLocaleString()} / 5,000</span>
            <button className="primary-button" type="submit" disabled={loading}>{loading ? "Listening..." : "Create my soundtrack ↗"}</button>
          </div>
        </form>
        {error && <p className="error" role="alert">{error}</p>}
        <div className="examples"><span>Try a starting point</span>{examples.map((example) => <button key={example} type="button" onClick={() => chooseExample(example)}>{example}</button>)}</div>
      </section>

      {soundtrack && <section className="results" aria-labelledby="results-title">
        <div className="results-header">
          <p className="eyebrow">Your soundtrack</p>
          <h2 id="results-title">{soundtrack.memory_analysis.memory_title}</h2>
          <p>{soundtrack.overall_explanation}</p>
          <div className="tags">{[...soundtrack.memory_analysis.primary_emotions, ...soundtrack.memory_analysis.themes].slice(0, 6).map((tag) => <span key={tag}>{tag}</span>)}</div>
          <form className="refinement-form" onSubmit={(event) => void submitRefinement(event)}><label className="sr-only" htmlFor="refinement">Refine this soundtrack</label><input id="refinement" value={refinement} onChange={(event) => setRefinement(event.target.value)} placeholder="Make it more nostalgic, peaceful, energetic, or Telugu…" maxLength={300} /><button type="submit" disabled={refining || !refinement.trim()}>{refining ? "Refining…" : "Refine ↗"}</button></form>
          {error && <p className="error" role="alert">{error}</p>}
        </div>
        <div className="track-list">
          {soundtrack.recommendations.map((track, index) => <article className="track" key={track.track_id}>
            <div className="track-number">{String(index + 1).padStart(2, "0")}</div>
            <div className="track-info"><h3>{track.track_name}</h3><p>{track.artist}{track.album ? ` · ${track.album}` : ""}</p><div className="track-meta">{track.language ?? "Language unavailable"} · {track.genre_tags.slice(0, 2).join(" · ")}</div><p className="reason">{track.explanation}</p></div>
            <div className="track-actions"><span className="score">{Math.round(track.relevance_score * 100)}%</span>{track.listening_url ? <a href={track.listening_url} target="_blank" rel="noreferrer">Listen ↗</a> : <span className="muted">Metadata only</span>}<div className="feedback" aria-label={`Feedback for ${track.track_name}`}>{["like", "dislike", "save"].map((type) => <button className={feedback[track.track_id] === type ? "selected" : ""} key={type} type="button" onClick={() => { void sendFeedback(track.track_id, type); setFeedback({ ...feedback, [track.track_id]: type }); }}>{type}</button>)}</div></div>
          </article>)}
        </div>
      </section>}

      </> : view === "vault" ? <section className="secondary-panel" aria-labelledby="vault-title">
        <p className="eyebrow">Your archive</p>
        <h1 id="vault-title">Memory vault</h1>
        <p className="panel-intro">The moments you chose to keep, with the soundtracks they opened.</p>
        {pageLoading && <p className="panel-status">Opening your vault…</p>}
        {pageError && <p className="error" role="alert">{pageError}</p>}
        {!pageLoading && !pageError && memories.length === 0 && <div className="empty-state"><strong>Your vault is quiet.</strong><span>Save a soundtrack and it will appear here.</span></div>}
        <div className="memory-grid">{memories.map((memoryItem) => <article className="memory-card" key={memoryItem.id}><div className="memory-card-top"><span>{new Date(memoryItem.created_at).toLocaleDateString()}</span><button type="button" onClick={() => void deleteMemory(memoryItem.id)} aria-label={`Delete ${memoryItem.memory_title}`}>Delete</button></div><h2>{memoryItem.memory_title}</h2><p>{memoryItem.summary}</p><div className="tags">{memoryItem.emotions.slice(0, 3).map((tag) => <span key={tag}>{tag}</span>)}</div><div className="memory-tracks">{memoryItem.recommendations.slice(0, 3).map((track) => <span key={`${memoryItem.id}-${track.track_name}`}>{track.track_name} · {track.artist}</span>)}</div></article>)}</div>
      </section> : <section className="secondary-panel" aria-labelledby="preferences-title">
        <p className="eyebrow">Tune the listening lens</p>
        <h1 id="preferences-title">Preferences</h1>
        <p className="panel-intro">A few signals help future soundtracks feel more like yours.</p>
        {pageLoading && !preferences && <p className="panel-status">Loading preferences…</p>}
        {pageError && <p className="error" role="alert">{pageError}</p>}
        {preferences && <form className="preferences-form" onSubmit={(event) => void savePreferences(event)}><label>Preferred languages<input value={preferences.preferred_languages.join(", ")} onChange={(event) => setPreferences({ ...preferences, preferred_languages: event.target.value.split(",").map((item) => item.trim()).filter(Boolean) })} placeholder="English, Telugu, Hindi" /></label><label>Preferred genres<input value={preferences.preferred_genres.join(", ")} onChange={(event) => setPreferences({ ...preferences, preferred_genres: event.target.value.split(",").map((item) => item.trim()).filter(Boolean) })} placeholder="Folk, ambient, acoustic" /></label><label>Genres to avoid<input value={preferences.disliked_genres.join(", ")} onChange={(event) => setPreferences({ ...preferences, disliked_genres: event.target.value.split(",").map((item) => item.trim()).filter(Boolean) })} placeholder="Genres you do not want" /></label><label>Explicit content<select value={preferences.explicit_content} onChange={(event) => setPreferences({ ...preferences, explicit_content: event.target.value as Preferences["explicit_content"] })}><option value="allow">Allow</option><option value="avoid">Avoid</option><option value="unknown">No preference</option></select></label><label>Recommendation diversity<input type="range" min="0" max="1" step="0.05" value={preferences.diversity} onChange={(event) => setPreferences({ ...preferences, diversity: Number(event.target.value) })} /><span className="range-value">{Math.round(preferences.diversity * 100)}%</span></label><button className="primary-button" type="submit" disabled={pageLoading}>{pageLoading ? "Saving…" : "Save preferences"}</button></form>}
      </section>}

      <footer><span>Every memory has a feeling. Every feeling has a sound.</span><span>Made for the moments that made you.</span></footer>
    </main>
  );
}
