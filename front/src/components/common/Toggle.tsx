export default function Toggle({ enabled, onChange }: { enabled: boolean; onChange: () => void }) {
  return (
    <button
      onClick={onChange}
      role="switch"
      aria-checked={enabled}
      className={`relative inline-flex h-[26px] w-11 items-center rounded-full transition-colors duration-150 ${enabled ? 'bg-success' : 'bg-[#e4e7ec]'}`}
    >
      <span
        className={`inline-block h-[22px] w-[22px] transform rounded-full bg-white shadow-seg transition-transform duration-150 ${enabled ? 'translate-x-[20px]' : 'translate-x-[2px]'}`}
      />
    </button>
  )
}
