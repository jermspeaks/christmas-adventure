export function ChoiceButton({ choice, onChoice }) {
  const handleClick = () => {
    onChoice(choice.target);
  };

  return (
    <button className="choice-btn" onClick={handleClick}>
      {choice.text}
    </button>
  );
}

