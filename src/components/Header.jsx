export function Header({ onReset }) {
  return (
    <div className="header">
      <h1>Choose Your Own Christmas Adventure</h1>
      <button id="reset-btn" onClick={onReset}>
        Start Over
      </button>
    </div>
  );
}

