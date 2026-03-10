import { useState, useRef } from "react";

/* ─────────────── constants ─────────────── */
const CATEGORIES = {
  hci:        { label: "MCI / Medieninformatik", color: "#7B1FA2" },
  design:     { label: "Design",                 color: "#C62828" },
  psychology: { label: "Psychologie",            color: "#2E7D32" },
  cs:         { label: "Informatik",             color: "#00695C" },
  math:       { label: "Mathematik",             color: "#1565C0" },
  elective:   { label: "Wahlpflicht",            color: "#E65100" },
};

const INITIAL_SEMESTERS = [
  { id: 1, modules: [
    { id:"CS1600",  code:"CS1600",      name:"Einführung in die Medieninformatik",         kp:4,  details:"2V+1Ü",    cat:"hci"        },
    { id:"CS1150",  code:"CS1150",      name:"Mediendesign und Medienproduktion",           kp:4,  details:"2V+1Ü",    cat:"design"     },
    { id:"PY2210",  code:"PY2210",      name:"Wahrnehmung und Kognition in MCI",            kp:4,  details:"2V+1S",    cat:"psychology" },
    { id:"CS1000",  code:"CS1000",      name:"Einführung in die Programmierung",            kp:10, details:"3V+3Ü+2P", cat:"cs"         },
    { id:"MA2000",  code:"MA2000",      name:"Analysis 1",                                  kp:8,  details:"4V+2Ü",    cat:"math"       },
  ]},
  { id: 2, modules: [
    { id:"CS2200",  code:"CS2200",      name:"Software-Ergonomie",                          kp:4,  details:"2V+1Ü",    cat:"hci"        },
    { id:"PY1802",  code:"PY1802",      name:"Statistik und Methoden der Nutzerforschung",  kp:8,  details:"2V+2S+1Ü", cat:"psychology" },
    { id:"CS1002",  code:"CS1002",      name:"Einführung in die Logik",                     kp:4,  details:"2V+1Ü",    cat:"cs"         },
    { id:"CS1001",  code:"CS1001",      name:"Algorithmen und Datenstrukturen",              kp:8,  details:"4V+2Ü",    cat:"cs"         },
    { id:"CS1200",  code:"CS1200",      name:"Technische Grundlagen der Informatik 1",       kp:6,  details:"2V+2Ü",    cat:"math"       },
  ]},
  { id: 3, modules: [
    { id:"CS2602a", code:"CS2602",      name:"Interaktive Systeme",                         kp:4,  details:"4V+2Ü",    cat:"hci"        },
    { id:"CS1601",  code:"CS1601",      name:"Grundlagen der Multimediatechnik",             kp:4,  details:"2V+1Ü",    cat:"design"     },
    { id:"CS2000",  code:"CS2000",      name:"Theoretische Informatik",                     kp:8,  details:"4V+2Ü",    cat:"cs"         },
    { id:"CS2300",  code:"CS2300",      name:"Software Engineering",                        kp:6,  details:"3V+1Ü",    cat:"cs"         },
    { id:"MA1000",  code:"MA1000",      name:"Lineare Algebra und Diskrete Strukturen 1",    kp:8,  details:"4V+2Ü",    cat:"math"       },
  ]},
  { id: 4, modules: [
    { id:"CS2602b", code:"CS2602",      name:"Interaktive Systeme",                         kp:4,  details:"4V+2Ü",    cat:"hci"        },
    { id:"CS2600",  code:"CS2600",      name:"Interaktionsdesign und User Experience",       kp:8,  details:"4V+2Ü",    cat:"design"     },
    { id:"PY2904",  code:"PY2904",      name:"Medienpsychologie",                           kp:4,  details:"2V+1S",    cat:"psychology" },
    { id:"CS2150",  code:"CS2150",      name:"Betriebssysteme und Netze",                   kp:8,  details:"4V+2Ü",    cat:"cs"         },
    { id:"CS2301",  code:"CS2301",      name:"Praktikum Software Engineering",              kp:6,  details:"4P",       cat:"cs"         },
  ]},
  { id: 5, modules: [
    { id:"CS3201",  code:"CS3201-KP04", name:"Usability- und UX-Engineering",               kp:4,  details:"2V+1Ü",    cat:"hci"        },
    { id:"CS3280",  code:"CS3280",      name:"Bachelor-Seminar Medieninformatik",            kp:4,  details:"2S",       cat:"hci"        },
    { id:"CS3210",  code:"CS3210",      name:"Bachelor-Projekt Medieninformatik",            kp:8,  details:"6P",       cat:"hci"        },
    { id:"CS3220",  code:"CS3220",      name:"Wissenschaftliches Arbeiten",                 kp:3,  details:"1V+1S",    cat:"elective"   },
    { id:"CS2700",  code:"CS2700",      name:"Datenbanken",                                 kp:4,  details:"2V+1Ü",    cat:"cs"         },
    { id:"WP5",     code:"—",           name:"Wahlpflicht (Platzhalter)",                   kp:7,  details:"nach Wahl",cat:"elective",  isPlaceholder:true },
  ]},
  { id: 6, modules: [
    { id:"CS3205",  code:"CS3205",      name:"Computergrafik",                              kp:4,  details:"2V+1Ü",    cat:"hci"        },
    { id:"CS3992",  code:"CS3992",      name:"Bachelorarbeit Medieninformatik",              kp:15, details:"",         cat:"hci"        },
    { id:"WP6",     code:"—",           name:"Wahlpflicht (Platzhalter)",                   kp:11, details:"nach Wahl",cat:"elective",  isPlaceholder:true },
  ]},
];

// Some example elective suggestions pre-loaded in the pool
const INITIAL_POOL = [
  { id:"pool1", code:"CS3100", name:"Mensch-Roboter-Interaktion",   kp:4, details:"2V+1Ü", cat:"hci"      },
  { id:"pool2", code:"CS3400", name:"Mobile Computing",             kp:4, details:"2V+1Ü", cat:"cs"       },
  { id:"pool3", code:"CS3500", name:"Informationsvisualisierung",   kp:4, details:"2V+1Ü", cat:"hci"      },
  { id:"pool4", code:"PY3100", name:"Arbeitspsychologie",           kp:4, details:"2V+1S", cat:"psychology"},
  { id:"pool5", code:"CS3600", name:"Game Design und Development",  kp:4, details:"2V+2P", cat:"design"   },
  { id:"pool6", code:"CS3700", name:"Machine Learning Grundlagen",  kp:4, details:"2V+1Ü", cat:"cs"       },
];

const BLANK = { code:"", name:"", kp:4, details:"", cat:"elective" };
let _uid = 2000;
const uid = () => `m${++_uid}`;

/* ─────────────── export / import ─────────────── */
const PLAN_VERSION = 2;

function exportPlan(semesters, pool) {
  const data = {
    version: PLAN_VERSION,
    exported: new Date().toISOString(),
    program: "Bachelor Medieninformatik - Universitat zu Lubeck",
    totalKP: semesters.reduce((a,s) => a + s.modules.reduce((b,m) => b + m.kp, 0), 0),
    semesters: semesters.map(s => ({
      semester: s.id,
      kp: s.modules.reduce((a,m) => a + m.kp, 0),
      modules: s.modules.map(m => ({
        code: m.code, name: m.name, kp: m.kp,
        details: m.details, category: CATEGORIES[m.cat]?.label ?? m.cat,
        cat: m.cat, isPlaceholder: m.isPlaceholder ?? false,
      })),
    })),
    wahlpflichtPool: pool.map(m => ({
      code: m.code, name: m.name, kp: m.kp,
      details: m.details, category: CATEGORIES[m.cat]?.label ?? m.cat, cat: m.cat,
    })),
  };
  const json = JSON.stringify(data, null, 2);
  const blob = new Blob([json], { type:"application/json" });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement("a");
  a.href = url;
  a.download = `studienplan_mi_luebeck_${new Date().toISOString().slice(0,10)}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

function parsePlan(json) {
  const data = JSON.parse(json);
  if (!data.semesters || !Array.isArray(data.semesters))
    throw new Error("Ungultiges Format: 'semesters' fehlt.");
  const validCats = Object.keys(CATEGORIES);
  const parseModule = (m, i, s) => {
    if (!m.name) throw new Error(`Modul ${i+1} in Semester ${s+1}: 'name' fehlt.`);
    return {
      id: uid(), code: m.code ?? "", name: m.name,
      kp: Number(m.kp)||0, details: m.details ?? "",
      cat: validCats.includes(m.cat) ? m.cat : "elective",
      isPlaceholder: m.isPlaceholder ?? false,
    };
  };
  const semesters = data.semesters.map((s,i) => {
    if (!Array.isArray(s.modules)) throw new Error(`Semester ${i+1}: 'modules' fehlt.`);
    return { id: s.semester ?? i+1, modules: s.modules.map((m,j) => parseModule(m,j,i)) };
  });
  const pool = Array.isArray(data.wahlpflichtPool)
    ? data.wahlpflichtPool.map((m,j) => ({ ...parseModule(m,j,0), isPlaceholder:false }))
    : [];
  return { semesters, pool };
}

/* ─────────────── main component ─────────────── */
export default function App() {
  const [semesters, setSemesters] = useState(INITIAL_SEMESTERS);
  const [pool,      setPool]      = useState(INITIAL_POOL);

  // drag: { moduleId, source: "semester"|"pool", semId? }
  const [drag,       setDrag]       = useState(null);
  // dropTarget for semester columns: { semId, moduleId|null, pos:"before"|"after"|null }
  const [dropTarget, setDropTarget] = useState(null);
  // dropTarget for pool: whether pool is highlighted as a drop zone
  const [poolDrop,   setPoolDrop]   = useState(false);
  // pool drop position between cards: { moduleId|null, pos }
  const [poolDropAt, setPoolDropAt] = useState(null);

  const [addSemId,   setAddSemId]   = useState(null);   // semId or "pool"
  const [editInfo,   setEditInfo]   = useState(null);   // { moduleId, source, semId? }
  const [delInfo,    setDelInfo]    = useState(null);   // { moduleId, source, semId? }
  const [form,       setForm]       = useState(BLANK);
  const [showLegend, setShowLegend] = useState(false);
  const [importError,setImportError]= useState(null);

  const dragNodeRef = useRef(null);
  const importRef   = useRef(null);

  const kpSum = sem => sem.modules.reduce((a,m) => a + m.kp, 0);
  const f = patch => setForm(p => ({ ...p, ...patch }));

  /* ─── generic helpers to extract a module from wherever it lives ─── */
  const removeFromSource = (mods, sem, pl, moduleId, source, semId) => {
    if (source === "pool") return { pool: pl.filter(m => m.id !== moduleId), semesters: sem };
    return {
      pool: pl,
      semesters: sem.map(s => s.id !== semId ? s : { ...s, modules: s.modules.filter(m => m.id !== moduleId) }),
    };
  };

  /* ─── drag handlers ─── */
  const onDragStart = (e, moduleId, source, semId) => {
    setDrag({ moduleId, source, semId });
    dragNodeRef.current = e.currentTarget;
    setTimeout(() => dragNodeRef.current?.classList.add("is-dragging"), 0);
  };
  const onDragEnd = () => {
    dragNodeRef.current?.classList.remove("is-dragging");
    setDrag(null); setDropTarget(null); setPoolDrop(false); setPoolDropAt(null);
  };

  /* ─── semester column drag-over ─── */
  const onModuleDragOver = (e, semId, moduleId) => {
    e.preventDefault(); e.stopPropagation();
    if (!drag || drag.moduleId === moduleId) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const pos  = e.clientY < rect.top + rect.height / 2 ? "before" : "after";
    setDropTarget({ semId, moduleId, pos });
    setPoolDrop(false); setPoolDropAt(null);
  };
  const onColDragOver = (e, semId) => {
    e.preventDefault();
    setDropTarget(dt => (!dt || dt.semId !== semId || dt.moduleId) ? { semId, moduleId:null, pos:null } : dt);
    setPoolDrop(false); setPoolDropAt(null);
  };

  /* ─── semester drop ─── */
  const onSemDrop = (e, semId) => {
    e.preventDefault();
    if (!drag) return;
    const dt = dropTarget ?? { semId, moduleId:null, pos:null };

    // Find the module being moved
    let mod;
    if (drag.source === "pool") {
      mod = pool.find(m => m.id === drag.moduleId);
    } else {
      mod = semesters.find(s => s.id === drag.semId)?.modules.find(m => m.id === drag.moduleId);
    }
    if (!mod) { onDragEnd(); return; }

    // Check if dropping onto a placeholder → replace it
    const targetSem = semesters.find(s => s.id === dt.semId ?? semId);
    const targetMod = dt.moduleId ? targetSem?.modules.find(m => m.id === dt.moduleId) : null;

    setSemesters(prev => {
      // 1. Remove from old semester (if from semester)
      let next = drag.source === "semester"
        ? prev.map(s => s.id !== drag.semId ? s : { ...s, modules: s.modules.filter(m => m.id !== drag.moduleId) })
        : prev.map(s => ({ ...s }));

      // 2. Insert into target semester
      next = next.map(s => {
        if (s.id !== (dt.semId ?? semId)) return s;
        const mods = [...s.modules];
        if (targetMod?.isPlaceholder) {
          // Replace placeholder: swap it out, keep same position
          const idx = mods.findIndex(m => m.id === dt.moduleId);
          mods.splice(idx, 1, { ...mod, isPlaceholder:false });
        } else if (!dt.moduleId) {
          mods.push({ ...mod, isPlaceholder:false });
        } else {
          let idx = mods.findIndex(m => m.id === dt.moduleId);
          if (dt.pos === "after") idx += 1;
          mods.splice(idx, 0, { ...mod, isPlaceholder:false });
        }
        return { ...s, modules: mods };
      });
      return next;
    });

    // Remove from pool if it came from pool
    if (drag.source === "pool") {
      setPool(prev => prev.filter(m => m.id !== drag.moduleId));
    }

    setDropTarget(null); setPoolDrop(false); setPoolDropAt(null);
    setDrag(null); dragNodeRef.current?.classList.remove("is-dragging");
  };

  /* ─── pool drag-over ─── */
  const onPoolCardDragOver = (e, moduleId) => {
    e.preventDefault(); e.stopPropagation();
    if (!drag || drag.moduleId === moduleId) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const pos  = e.clientX < rect.left + rect.width / 2 ? "before" : "after";
    setPoolDropAt({ moduleId, pos });
    setPoolDrop(true);
    setDropTarget(null);
  };
  const onPoolAreaDragOver = (e) => {
    e.preventDefault();
    setPoolDrop(true);
    setDropTarget(null);
  };

  /* ─── pool drop ─── */
  const onPoolDrop = (e) => {
    e.preventDefault();
    if (!drag) return;

    let mod;
    if (drag.source === "pool") {
      mod = pool.find(m => m.id === drag.moduleId);
    } else {
      mod = semesters.find(s => s.id === drag.semId)?.modules.find(m => m.id === drag.moduleId);
    }
    if (!mod) { onDragEnd(); return; }

    // Remove from semester if from semester
    if (drag.source === "semester") {
      setSemesters(prev => prev.map(s => s.id !== drag.semId ? s :
        { ...s, modules: s.modules.filter(m => m.id !== drag.moduleId) }
      ));
    }

    // Insert into pool at correct position
    setPool(prev => {
      const next = drag.source === "pool" ? prev.filter(m => m.id !== drag.moduleId) : [...prev];
      if (!poolDropAt || !poolDropAt.moduleId) {
        next.push({ ...mod, isPlaceholder:false });
      } else {
        let idx = next.findIndex(m => m.id === poolDropAt.moduleId);
        if (poolDropAt.pos === "after") idx += 1;
        next.splice(idx, 0, { ...mod, isPlaceholder:false });
      }
      return next;
    });

    setPoolDrop(false); setPoolDropAt(null); setDropTarget(null);
    setDrag(null); dragNodeRef.current?.classList.remove("is-dragging");
  };

  /* ─── CRUD ─── */
  const doDelete = () => {
    if (delInfo.source === "pool") {
      setPool(prev => prev.filter(m => m.id !== delInfo.moduleId));
    } else {
      setSemesters(prev => prev.map(s => s.id !== delInfo.semId ? s :
        { ...s, modules: s.modules.filter(m => m.id !== delInfo.moduleId) }
      ));
    }
    setDelInfo(null);
  };

  const openEdit = (mod, source, semId) => {
    setEditInfo({ moduleId:mod.id, source, semId });
    setForm({ code:mod.code, name:mod.name, kp:mod.kp, details:mod.details, cat:mod.cat });
  };

  const doEdit = () => {
    if (!form.name.trim()) return;
    const patch = { ...form, kp: Math.max(0, Number(form.kp)||0) };
    if (editInfo.source === "pool") {
      setPool(prev => prev.map(m => m.id !== editInfo.moduleId ? m : { ...m, ...patch }));
    } else {
      setSemesters(prev => prev.map(s => s.id !== editInfo.semId ? s : {
        ...s, modules: s.modules.map(m => m.id !== editInfo.moduleId ? m : { ...m, ...patch }),
      }));
    }
    setEditInfo(null);
  };

  const doAdd = () => {
    if (!form.name.trim()) return;
    const mod = { ...form, id:uid(), kp: Math.max(0, Number(form.kp)||0), isPlaceholder:false };
    if (addSemId === "pool") {
      setPool(prev => [...prev, mod]);
    } else {
      setSemesters(prev => prev.map(s => s.id !== addSemId ? s :
        { ...s, modules: [...s.modules, mod] }
      ));
    }
    setAddSemId(null);
  };

  const handleImport = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      try {
        const { semesters: s, pool: p } = parsePlan(ev.target.result);
        setSemesters(s); setPool(p); setImportError(null);
      } catch (err) { setImportError(err.message); }
    };
    reader.readAsText(file);
    e.target.value = "";
  };

  /* ─── render ─── */
  return (
    <div style={S.page}>
      <style>{`
        * { box-sizing:border-box; }
        .mod-card { position:relative; transition:transform .12s, box-shadow .12s; }
        .mod-card:hover { transform:translateY(-1px); box-shadow:0 8px 20px rgba(0,0,0,.32) !important; }
        .mod-actions { opacity:0; transition:opacity .15s; pointer-events:none; }
        .mod-card:hover .mod-actions { opacity:1; pointer-events:all; }
        .is-dragging { opacity:.22 !important; transform:scale(.96); }
        .add-btn:hover { background:#E4E4E4 !important; }
        .pool-card:hover .mod-actions { opacity:1; pointer-events:all; }
        input:focus, select:focus { outline:2px solid #7B1FA2; border-color:transparent; }
        .drop-line-before::before { content:""; display:block; height:3px; background:#7B1FA2; border-radius:2px; margin-bottom:4px; }
        .drop-line-after::after  { content:""; display:block; height:3px; background:#7B1FA2; border-radius:2px; margin-top:4px; }
        .pool-drop-left::before  { content:""; display:block; width:3px; background:#E65100; border-radius:2px; position:absolute; left:-6px; top:0; bottom:0; }
        .pool-drop-right::after  { content:""; display:block; width:3px; background:#E65100; border-radius:2px; position:absolute; right:-6px; top:0; bottom:0; }
        .placeholder-card { opacity:.7; background: repeating-linear-gradient(45deg,transparent,transparent 4px,rgba(255,255,255,.08) 4px,rgba(255,255,255,.08) 8px) !important; border:2px dashed rgba(255,255,255,.5) !important; }
      `}</style>

      {/* Header */}
      <header style={S.header}>
        <div>
          <div style={S.eyebrow}>Universität zu Lübeck</div>
          <h1 style={S.h1}>Bachelor Medieninformatik</h1>
          <p style={S.sub}>Studienverlaufsplaner — verschieben · sortieren · bearbeiten</p>
        </div>
        <div style={{ display:"flex", gap:8, flexWrap:"wrap", alignItems:"center" }}>
          <button style={S.ghost} onClick={() => setShowLegend(v => !v)}>Legende</button>
          <button style={S.ghost} onClick={() => { setSemesters(INITIAL_SEMESTERS); setPool(INITIAL_POOL); }}>Zurücksetzen</button>
          <div style={S.divider} />
          <button style={S.ghostGreen} onClick={() => exportPlan(semesters, pool)}>↓ Exportieren</button>
          <button style={S.ghostGreen} onClick={() => importRef.current?.click()}>↑ Importieren</button>
          <input ref={importRef} type="file" accept=".json" style={{ display:"none" }} onChange={handleImport} />
        </div>
      </header>

      {showLegend && (
        <div style={S.legend}>
          {Object.entries(CATEGORIES).map(([k,v]) => (
            <span key={k} style={S.legItem}>
              <span style={{ ...S.legDot, background:v.color }} />{v.label}
            </span>
          ))}
        </div>
      )}

      {/* ── Semester grid ── */}
      <div style={S.grid}>
        {semesters.map(sem => {
          const kp    = kpSum(sem);
          const delta = kp - 30;
          const bc    = delta === 0 ? "#2E7D32" : delta > 0 ? "#C62828" : "#E65100";
          const colHl = dropTarget?.semId === sem.id;

          return (
            <div key={sem.id}
              style={{ ...S.col, ...(colHl ? S.colHl : {}) }}
              onDragOver={e => onColDragOver(e, sem.id)}
              onDragLeave={e => { if (!e.currentTarget.contains(e.relatedTarget)) setDropTarget(null); }}
              onDrop={e => onSemDrop(e, sem.id)}
            >
              <div style={S.colHead}>
                <span style={S.semNum}>{sem.id}. Semester</span>
                <span style={{ ...S.badge, background:bc }}>{kp} KP</span>
              </div>

              <div style={S.mList}>
                {sem.modules.map(mod => {
                  const color  = CATEGORIES[mod.cat]?.color ?? "#555";
                  const isBefore = dropTarget?.moduleId === mod.id && dropTarget?.pos === "before";
                  const isAfter  = dropTarget?.moduleId === mod.id && dropTarget?.pos === "after";

                  return (
                    <div key={mod.id}
                      className={`mod-card${isBefore?" drop-line-before":""}${isAfter?" drop-line-after":""}`}
                      draggable
                      onDragStart={e => onDragStart(e, mod.id, "semester", sem.id)}
                      onDragEnd={onDragEnd}
                      onDragOver={e => onModuleDragOver(e, sem.id, mod.id)}
                    >
                      <div style={{ ...S.cardInner, background:color, minHeight:Math.max(52, mod.kp*7) }}
                        className={mod.isPlaceholder ? "placeholder-card" : ""}>
                        {mod.isPlaceholder && <div style={S.placeholderTag}>Platzhalter</div>}
                        <div style={S.mCode}>{mod.code}</div>
                        <div style={S.mName}>{mod.name}</div>
                        <div style={S.mFoot}>
                          <span style={S.mKP}>{mod.kp} KP</span>
                          {mod.details && <span style={S.mDet}>{mod.details}</span>}
                        </div>
                        <div className="mod-actions" style={S.actionBar}>
                          <button style={S.actionBtn}
                            onClick={e => { e.stopPropagation(); openEdit(mod, "semester", sem.id); }}>
                            ✎ Bearbeiten
                          </button>
                          <button style={{ ...S.actionBtn, background:"rgba(180,0,0,.55)" }}
                            onClick={e => { e.stopPropagation(); setDelInfo({ moduleId:mod.id, source:"semester", semId:sem.id }); }}>
                            ✕ Entfernen
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                })}
                {colHl && drag && sem.modules.length === 0 && (
                  <div style={S.emptyDrop}>Hier ablegen</div>
                )}
              </div>

              <button className="add-btn" style={S.addBtn}
                onClick={() => { setAddSemId(sem.id); setForm(BLANK); }}>
                <span style={{ color:"#7B1FA2", fontSize:16, fontWeight:700 }}>+</span>
                Modul hinzufügen
              </button>
              <div style={{ ...S.colFoot, color:bc }}>
                {delta === 0 ? "✓ 30 / 30 KP" : delta > 0 ? `⚠ ${kp} KP (+${delta} zu viel)` : `⚠ ${kp} KP (${Math.abs(delta)} fehlen)`}
              </div>
            </div>
          );
        })}
      </div>

      {/* ── Wahlpflicht Pool ── */}
      <div style={{ padding:"0 12px 8px" }}>
        <div
          style={{ ...S.poolArea, ...(poolDrop ? S.poolAreaHl : {}) }}
          onDragOver={onPoolAreaDragOver}
          onDragLeave={e => { if (!e.currentTarget.contains(e.relatedTarget)) { setPoolDrop(false); setPoolDropAt(null); }}}
          onDrop={onPoolDrop}
        >
          {/* Pool header */}
          <div style={S.poolHead}>
            <div>
              <span style={S.poolTitle}>Wahlpflicht-Module</span>
              <span style={S.poolSub}>
                Ziehe Module in die Semester (ersetzt Platzhalter) · Ziehe Semester-Module hierher zurück
              </span>
            </div>
            <div style={{ display:"flex", gap:8, alignItems:"center" }}>
              <span style={S.poolKpTotal}>
                {pool.reduce((a,m) => a+m.kp, 0)} KP verfügbar
              </span>
              <button className="add-btn" style={{ ...S.addBtn, margin:0, padding:"5px 14px", width:"auto" }}
                onClick={() => { setAddSemId("pool"); setForm({ ...BLANK, cat:"elective" }); }}>
                <span style={{ color:"#E65100", fontSize:16, fontWeight:700 }}>+</span>
                Hinzufügen
              </button>
            </div>
          </div>

          {/* Pool cards */}
          <div style={S.poolCards}>
            {pool.length === 0 && !poolDrop && (
              <div style={S.poolEmpty}>
                Noch keine Wahlpflichtmodule — füge welche hinzu oder ziehe Module aus den Semestern hierher.
              </div>
            )}

            {pool.map(mod => {
              const color = CATEGORIES[mod.cat]?.color ?? "#E65100";
              const isLeft  = poolDropAt?.moduleId === mod.id && poolDropAt?.pos === "before";
              const isRight = poolDropAt?.moduleId === mod.id && poolDropAt?.pos === "after";
              return (
                <div key={mod.id}
                  className={`mod-card pool-card${isLeft?" pool-drop-left":""}${isRight?" pool-drop-right":""}`}
                  style={{ position:"relative" }}
                  draggable
                  onDragStart={e => onDragStart(e, mod.id, "pool")}
                  onDragEnd={onDragEnd}
                  onDragOver={e => onPoolCardDragOver(e, mod.id)}
                >
                  <div style={{ ...S.poolCard, background:color }}>
                    <div style={S.mCode}>{mod.code}</div>
                    <div style={{ ...S.mName, fontSize:12 }}>{mod.name}</div>
                    <div style={S.mFoot}>
                      <span style={S.mKP}>{mod.kp} KP</span>
                      {mod.details && <span style={S.mDet}>{mod.details}</span>}
                    </div>
                    <div className="mod-actions" style={S.actionBar}>
                      <button style={S.actionBtn}
                        onClick={e => { e.stopPropagation(); openEdit(mod, "pool"); }}>
                        ✎
                      </button>
                      <button style={{ ...S.actionBtn, background:"rgba(180,0,0,.55)" }}
                        onClick={e => { e.stopPropagation(); setDelInfo({ moduleId:mod.id, source:"pool" }); }}>
                        ✕
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}

            {poolDrop && drag && drag.source !== "pool" && (
              <div style={S.poolDropHint}>Hier ablegen</div>
            )}
          </div>
        </div>
      </div>

      <p style={S.hint}>Drag &amp; Drop zum Verschieben · Wahlpflicht-Module in Platzhalter ziehen zum Ersetzen · Hover für Aktionen</p>

      {importError && (
        <div style={S.toast}>
          <span>⚠ Import fehlgeschlagen: {importError}</span>
          <button style={S.toastClose} onClick={() => setImportError(null)}>✕</button>
        </div>
      )}

      {/* ── Add Modal ── */}
      {addSemId !== null && (
        <Modal title={addSemId === "pool" ? "Wahlpflichtmodul hinzufügen" : `Modul hinzufügen — ${addSemId}. Semester`}
          onClose={() => setAddSemId(null)}>
          <ModuleForm form={form} f={f} />
          <div style={S.mActions}>
            <button style={S.btnSec} onClick={() => setAddSemId(null)}>Abbrechen</button>
            <button style={{ ...S.btnPri, opacity:form.name.trim()?1:.4 }}
              onClick={doAdd} disabled={!form.name.trim()}>Hinzufügen</button>
          </div>
        </Modal>
      )}

      {/* ── Edit Modal ── */}
      {editInfo && (
        <Modal title={editInfo.source === "pool" ? "Wahlpflichtmodul bearbeiten" : `Modul bearbeiten — ${editInfo.semId}. Semester`}
          onClose={() => setEditInfo(null)}>
          <ModuleForm form={form} f={f} />
          <div style={S.mActions}>
            <button style={S.btnSec} onClick={() => setEditInfo(null)}>Abbrechen</button>
            <button style={{ ...S.btnPri, opacity:form.name.trim()?1:.4 }}
              onClick={doEdit} disabled={!form.name.trim()}>Speichern</button>
          </div>
        </Modal>
      )}

      {/* ── Delete Confirm ── */}
      {delInfo && (() => {
        const mod = delInfo.source === "pool"
          ? pool.find(m => m.id === delInfo.moduleId)
          : semesters.find(s => s.id === delInfo.semId)?.modules.find(m => m.id === delInfo.moduleId);
        return (
          <Modal title="Modul entfernen" onClose={() => setDelInfo(null)}>
            <p style={{ fontSize:14, color:"#333", margin:"4px 0 16px", lineHeight:1.6 }}>
              <strong>„{mod?.name}"</strong> ({mod?.kp} KP) entfernen?
            </p>
            <div style={S.mActions}>
              <button style={S.btnSec} onClick={() => setDelInfo(null)}>Abbrechen</button>
              <button style={S.btnDanger} onClick={doDelete}>Entfernen</button>
            </div>
          </Modal>
        );
      })()}
    </div>
  );
}

/* ─────────────── sub-components ─────────────── */
function Modal({ title, onClose, children }) {
  return (
    <div style={S.overlay} onClick={onClose}>
      <div style={S.modal} onClick={e => e.stopPropagation()}>
        <div style={S.mhRow}>
          <span style={S.mhTitle}>{title}</span>
          <button style={S.xBtn} onClick={onClose}>✕</button>
        </div>
        {children}
      </div>
    </div>
  );
}

function Field({ label, children, style }) {
  return (
    <div style={{ marginBottom:14, ...style }}>
      <label style={S.lbl}>{label}</label>
      {children}
    </div>
  );
}

function ModuleForm({ form, f }) {
  return (
    <>
      <Field label="Modulcode">
        <input style={S.inp} placeholder="z.B. CS9999"
          value={form.code} onChange={e => f({ code:e.target.value })} />
      </Field>
      <Field label="Modulname *">
        <input style={S.inp} placeholder="Name des Moduls"
          value={form.name} onChange={e => f({ name:e.target.value })} />
      </Field>
      <div style={{ display:"flex", gap:12 }}>
        <Field label="KP" style={{ flex:1 }}>
          <input style={S.inp} type="number" min={1} max={30}
            value={form.kp} onChange={e => f({ kp:e.target.value })} />
        </Field>
        <Field label="Format" style={{ flex:1 }}>
          <input style={S.inp} placeholder="2V+1Ü"
            value={form.details} onChange={e => f({ details:e.target.value })} />
        </Field>
      </div>
      <Field label="Kategorie">
        <div style={{ position:"relative" }}>
          <select style={S.sel} value={form.cat} onChange={e => f({ cat:e.target.value })}>
            {Object.entries(CATEGORIES).map(([k,v]) => (
              <option key={k} value={k}>{v.label}</option>
            ))}
          </select>
          <span style={{ ...S.catDot, background:CATEGORIES[form.cat].color }} />
        </div>
      </Field>
    </>
  );
}

/* ─────────────── styles ─────────────── */
const S = {
  page:      { fontFamily:"system-ui,sans-serif", minHeight:"100vh", background:"#EFEFEA", paddingBottom:40 },
  header:    { background:"#1a1a2e", color:"white", padding:"22px 28px", display:"flex", justifyContent:"space-between", alignItems:"center", flexWrap:"wrap", gap:12, borderBottom:"4px solid #7B1FA2" },
  eyebrow:   { fontSize:10, letterSpacing:"0.14em", textTransform:"uppercase", color:"#888", marginBottom:3 },
  h1:        { margin:0, fontSize:21, fontWeight:700, fontFamily:"Georgia,serif" },
  sub:       { margin:"4px 0 0", fontSize:12, color:"#aaa" },
  ghost:     { background:"transparent", border:"1px solid rgba(255,255,255,.3)", color:"white", padding:"6px 14px", borderRadius:4, cursor:"pointer", fontSize:12 },
  divider:   { width:1, height:24, background:"rgba(255,255,255,.2)", margin:"0 2px" },
  ghostGreen:{ background:"rgba(46,125,50,.25)", border:"1px solid rgba(100,220,100,.4)", color:"#aeffae", padding:"6px 14px", borderRadius:4, cursor:"pointer", fontSize:12, fontWeight:600 },
  legend:    { display:"flex", flexWrap:"wrap", gap:"6px 20px", padding:"10px 28px", background:"#FAFAFA", borderBottom:"1px solid #DDD" },
  legItem:   { display:"flex", alignItems:"center", gap:6, fontSize:12, color:"#444" },
  legDot:    { width:10, height:10, borderRadius:"50%", flexShrink:0 },

  grid:      { display:"grid", gridTemplateColumns:"repeat(6,1fr)", gap:0, padding:"18px 12px 10px", overflowX:"auto", minWidth:920 },
  col:       { background:"white", borderRadius:8, margin:"0 5px", display:"flex", flexDirection:"column", border:"2px solid transparent", transition:"border-color .15s, box-shadow .15s", boxShadow:"0 1px 4px rgba(0,0,0,.07)" },
  colHl:     { borderColor:"#7B1FA2", boxShadow:"0 0 0 3px rgba(123,31,162,.15)" },
  colHead:   { padding:"10px 10px 8px", borderBottom:"1px solid #EEE", display:"flex", justifyContent:"space-between", alignItems:"center" },
  semNum:    { fontWeight:700, fontSize:12, color:"#222" },
  badge:     { color:"white", fontSize:10, fontWeight:700, padding:"2px 7px", borderRadius:10 },
  mList:     { flex:1, padding:"7px 7px 3px", display:"flex", flexDirection:"column" },
  cardInner: { borderRadius:5, padding:"7px 9px", color:"white", userSelect:"none", cursor:"grab", boxShadow:"0 2px 5px rgba(0,0,0,.22)", position:"relative", overflow:"hidden" },
  placeholderTag: { position:"absolute", top:4, right:4, fontSize:8, background:"rgba(0,0,0,.3)", color:"white", padding:"1px 5px", borderRadius:3, letterSpacing:"0.05em", textTransform:"uppercase" },
  mCode:     { fontSize:9, opacity:.8, marginBottom:2, letterSpacing:"0.03em" },
  mName:     { fontSize:11, fontWeight:700, lineHeight:1.35, marginBottom:4 },
  mFoot:     { display:"flex", justifyContent:"space-between", alignItems:"center" },
  mKP:       { fontSize:10, fontWeight:700, background:"rgba(0,0,0,.2)", padding:"1px 6px", borderRadius:3 },
  mDet:      { fontSize:9, opacity:.8 },
  actionBar: { position:"absolute", bottom:0, left:0, right:0, display:"flex", background:"rgba(0,0,0,.45)" },
  actionBtn: { flex:1, padding:"5px 4px", background:"transparent", border:"none", color:"white", cursor:"pointer", fontSize:10, fontWeight:600, transition:"background .12s" },
  emptyDrop: { border:"2px dashed #7B1FA2", borderRadius:5, padding:14, textAlign:"center", color:"#7B1FA2", fontSize:11, background:"rgba(123,31,162,.04)", margin:"4px 0" },
  addBtn:    { margin:"6px 7px 4px", padding:"7px 0", background:"#F0F0F0", border:"1px dashed #CCC", borderRadius:5, cursor:"pointer", fontSize:11, color:"#666", display:"flex", alignItems:"center", justifyContent:"center", gap:5, transition:"background .15s" },
  colFoot:   { padding:"5px 10px 9px", fontSize:10, textAlign:"center" },

  /* pool */
  poolArea:     { background:"white", borderRadius:10, border:"2px solid #E0E0E0", padding:"14px 16px 16px", transition:"border-color .15s, box-shadow .15s" },
  poolAreaHl:   { borderColor:"#E65100", boxShadow:"0 0 0 3px rgba(230,81,0,.15)" },
  poolHead:     { display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:12, flexWrap:"wrap", gap:8 },
  poolTitle:    { fontWeight:700, fontSize:14, color:"#222", marginRight:10 },
  poolSub:      { fontSize:11, color:"#888" },
  poolKpTotal:  { fontSize:11, fontWeight:700, color:"#E65100", background:"#FFF3E0", padding:"3px 10px", borderRadius:10 },
  poolCards:    { display:"flex", flexWrap:"wrap", gap:8, minHeight:52, alignItems:"flex-start" },
  poolCard:     { borderRadius:5, padding:"7px 10px", color:"white", cursor:"grab", userSelect:"none", width:170, minHeight:72, boxShadow:"0 2px 5px rgba(0,0,0,.2)", position:"relative", overflow:"hidden", flexShrink:0 },
  poolEmpty:    { fontSize:12, color:"#AAA", fontStyle:"italic", padding:"10px 4px" },
  poolDropHint: { border:"2px dashed #E65100", borderRadius:5, padding:"10px 18px", textAlign:"center", color:"#E65100", fontSize:11, background:"rgba(230,81,0,.04)", alignSelf:"stretch", display:"flex", alignItems:"center" },

  hint:      { textAlign:"center", fontSize:12, color:"#999", marginTop:6, padding:"0 12px" },
  toast:     { position:"fixed", bottom:24, left:"50%", transform:"translateX(-50%)", background:"#C62828", color:"white", padding:"11px 18px", borderRadius:8, display:"flex", alignItems:"center", gap:14, fontSize:13, boxShadow:"0 4px 20px rgba(0,0,0,.35)", zIndex:300, maxWidth:520 },
  toastClose:{ background:"none", border:"none", color:"white", fontSize:18, cursor:"pointer", lineHeight:1, padding:0 },

  overlay:  { position:"fixed", inset:0, background:"rgba(0,0,0,.5)", display:"flex", alignItems:"center", justifyContent:"center", zIndex:200 },
  modal:    { background:"white", borderRadius:10, padding:"22px", width:"100%", maxWidth:440, boxShadow:"0 20px 60px rgba(0,0,0,.3)" },
  mhRow:    { display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:18 },
  mhTitle:  { fontWeight:700, fontSize:14, color:"#222" },
  xBtn:     { background:"none", border:"none", fontSize:18, cursor:"pointer", color:"#888", lineHeight:1 },
  lbl:      { display:"block", fontSize:10, fontWeight:700, color:"#555", marginBottom:5, textTransform:"uppercase", letterSpacing:"0.06em" },
  inp:      { width:"100%", padding:"8px 10px", border:"1px solid #DDD", borderRadius:5, fontSize:13 },
  sel:      { width:"100%", padding:"8px 32px 8px 10px", border:"1px solid #DDD", borderRadius:5, fontSize:13, appearance:"none" },
  catDot:   { position:"absolute", right:10, top:"50%", transform:"translateY(-50%)", width:14, height:14, borderRadius:3, pointerEvents:"none" },
  mActions: { display:"flex", justifyContent:"flex-end", gap:9, marginTop:18 },
  btnSec:   { padding:"7px 16px", background:"#F5F5F5", border:"1px solid #DDD", borderRadius:5, cursor:"pointer", fontSize:13 },
  btnPri:   { padding:"7px 18px", background:"#7B1FA2", color:"white", border:"none", borderRadius:5, cursor:"pointer", fontSize:13, fontWeight:600 },
  btnDanger:{ padding:"7px 18px", background:"#C62828", color:"white", border:"none", borderRadius:5, cursor:"pointer", fontSize:13, fontWeight:600 },
};
