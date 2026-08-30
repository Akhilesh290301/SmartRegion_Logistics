APP_CSS = """
<style>
.stApp {
    background:
        radial-gradient(
            circle at top left,
            rgba(59,130,246,0.10),
            transparent 32%
        ),
        radial-gradient(
            circle at top right,
            rgba(20,184,166,0.10),
            transparent 30%
        ),
        #f6f8fc;
}

.block-container {
    padding-top: 3rem !important;
    padding-bottom: 3rem !important;
    max-width: 1450px !important;
}

header[data-testid="stHeader"] {
    background: transparent;
}

.hero-wrapper {
    position: relative;
    overflow: hidden;
    padding: 42px;
    margin-top: 14px;
    margin-bottom: 28px;
    border-radius: 26px;
    background: linear-gradient(
        120deg,
        #102a43 0%,
        #145da0 38%,
        #168aad 68%,
        #1fa2a6 100%
    );
    box-shadow: 0 20px 55px rgba(16,42,67,0.20);
    color: white;
}

.hero-wrapper::before {
    content: "";
    position: absolute;
    width: 330px;
    height: 330px;
    border-radius: 50%;
    background: rgba(255,255,255,0.07);
    right: -90px;
    top: -175px;
}

.hero-wrapper::after {
    content: "";
    position: absolute;
    width: 220px;
    height: 220px;
    border-radius: 50%;
    background: rgba(255,255,255,0.06);
    right: 130px;
    bottom: -150px;
}

.hero-badge {
    display: inline-block;
    padding: 7px 14px;
    margin-bottom: 18px;
    border-radius: 999px;
    background: rgba(255,255,255,0.14);
    border: 1px solid rgba(255,255,255,0.22);
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.5px;
    position: relative;
    z-index: 2;
}

.hero-title {
    margin: 0 !important;
    padding: 0 !important;
    color: white !important;
    font-size: clamp(35px, 4vw, 58px);
    line-height: 1.12 !important;
    font-weight: 850;
    letter-spacing: -1.5px;
    position: relative;
    z-index: 2;
}

.hero-highlight {
    color: #9ef0e8;
}

.hero-subtitle {
    margin-top: 15px;
    max-width: 900px;
    color: rgba(255,255,255,0.90);
    font-size: 17px;
    line-height: 1.65;
    position: relative;
    z-index: 2;
}

.hero-tags {
    display: flex;
    gap: 9px;
    flex-wrap: wrap;
    margin-top: 22px;
    position: relative;
    z-index: 2;
}

.hero-tag {
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.18);
    color: white;
    padding: 7px 12px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 650;
}

.section-heading {
    font-size: 25px;
    font-weight: 820;
    color: #102a43;
    margin-top: 10px;
    margin-bottom: 4px;
}

.section-description {
    font-size: 14px;
    color: #64748b;
    margin-bottom: 18px;
}

.info-card {
    background: white;
    padding: 22px;
    border-radius: 18px;
    border: 1px solid #e5eaf1;
    box-shadow: 0 7px 25px rgba(15,23,42,0.05);
    min-height: 145px;
}

.card-label {
    color: #64748b;
    font-size: 12px;
    font-weight: 750;
    text-transform: uppercase;
    letter-spacing: 0.7px;
}

.card-value {
    margin-top: 6px;
    color: #102a43;
    font-weight: 850;
    font-size: 25px;
}

.card-value-small {
    font-size: 18px;
}

.card-value-medium {
    font-size: 21px;
}

.card-small {
    margin-top: 8px;
    color: #64748b;
    font-size: 13px;
    line-height: 1.45;
}

.match-card {
    background: white;
    border-radius: 20px;
    padding: 22px 24px;
    margin-bottom: 18px;
    border: 1px solid #e3e9f2;
    box-shadow: 0 8px 28px rgba(15,23,42,0.06);
}

.match-flex {
    display: flex;
    justify-content: space-between;
    gap: 20px;
    align-items: flex-start;
}

.company-name {
    color: #102a43;
    font-size: 21px;
    font-weight: 820;
    margin-bottom: 5px;
}

.company-meta {
    color: #64748b;
    font-size: 13px;
}

.score {
    font-size: 30px;
    font-weight: 900;
    color: #087f8c;
    text-align: right;
}

.score-label {
    text-align: right;
    color: #64748b;
    font-size: 12px;
    font-weight: 650;
}

.status-good,
.status-partial,
.status-bad {
    display: inline-block;
    margin-top: 9px;
    padding: 6px 11px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 750;
}

.status-good {
    background: #dcfce7;
    color: #166534;
}

.status-partial {
    background: #fef3c7;
    color: #92400e;
}

.status-bad {
    background: #fee2e2;
    color: #991b1b;
}

.stButton > button {
    width: 100%;
    border-radius: 12px;
    min-height: 48px;
    font-weight: 750;
    background: linear-gradient(90deg, #145da0, #168aad);
    color: white;
    border: 0;
    box-shadow: 0 7px 18px rgba(20,93,160,0.18);
}

.stButton > button:hover {
    background: linear-gradient(90deg, #124f89, #127b91);
    color: white;
    border: 0;
}

div[data-baseweb="select"] > div,
.stTextInput input,
.stNumberInput input {
    border-radius: 11px !important;
}

.footer {
    margin-top: 45px;
    padding-top: 18px;
    border-top: 1px solid #e2e8f0;
    text-align: center;
    color: #94a3b8;
    font-size: 12px;
}

@media (max-width: 800px) {
    .block-container {
        padding-top: 1.7rem !important;
    }

    .hero-wrapper {
        padding: 30px 24px;
    }

    .hero-title {
        font-size: 34px;
    }

    .hero-subtitle {
        font-size: 15px;
    }

    .match-flex {
        flex-direction: column;
    }

    .score,
    .score-label {
        text-align: left;
    }
}
</style>
"""