export const logoSvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="-80 -80 160 160" width="32" height="32">
  <defs>
    <path id="p" d="M0,0 C-15,-10 -31,-30 -23,-54 C-19,-65 -8,-63 0,-52 C8,-63 19,-65 23,-54 C31,-30 15,-10 0,0 Z"/>
    <clipPath id="c"><use href="#p"/></clipPath>

    <g id="pet">
      <use href="#p" fill="#ffc4da"/>
      <g clip-path="url(#c)">
        <path d="M24,-60 C33,-30 15,-10 0,1 C11,-20 17,-38 9,-66 Z" fill="#f7a3c3"/>
        <path d="M0,2 C-10,-6 -16,-18 -12,-30 C-6,-26 6,-26 12,-30 C16,-18 10,-6 0,2 Z" fill="#ff86b2"/>
        <path d="M0,-8 L0,-40 M0,-10 L-10,-38 M0,-10 L10,-38" fill="none" stroke="#e8689b" stroke-width="1.3" stroke-linecap="round"/>
      </g>
      <use href="#p" fill="none" stroke="#4a1d3f" stroke-width="3" stroke-linejoin="round"/>
      <path d="M-19,-50 C-24,-41 -23,-31 -18,-23" fill="none" stroke="#fff" stroke-width="2.6" stroke-linecap="round"/>
      <circle cx="-22" cy="-17" r="1.5" fill="#fff"/>
    </g>

    <g id="s1">
      <path d="M0,-6 L0,-21" stroke="#4a1d3f" stroke-width="3.4" stroke-linecap="round"/>
      <path d="M0,-6 L0,-21" stroke="#ff7fae" stroke-width="1.4" stroke-linecap="round"/>
      <circle cy="-23" r="3.4" fill="#ffd166" stroke="#4a1d3f" stroke-width="1.8"/>
    </g>
    <g id="s2">
      <path d="M0,-6 L0,-27" stroke="#4a1d3f" stroke-width="3.4" stroke-linecap="round"/>
      <path d="M0,-6 L0,-27" stroke="#ff7fae" stroke-width="1.4" stroke-linecap="round"/>
      <circle cy="-29" r="3.4" fill="#ffd166" stroke="#4a1d3f" stroke-width="1.8"/>
    </g>
  </defs>

  <use href="#pet"/>
  <use href="#pet" transform="rotate(72)"/>
  <use href="#pet" transform="rotate(144)"/>
  <use href="#pet" transform="rotate(216)"/>
  <use href="#pet" transform="rotate(288)"/>

  <use href="#s1" transform="rotate(18)"/>
  <use href="#s2" transform="rotate(54)"/>
  <use href="#s1" transform="rotate(90)"/>
  <use href="#s2" transform="rotate(126)"/>
  <use href="#s1" transform="rotate(162)"/>
  <use href="#s2" transform="rotate(198)"/>
  <use href="#s1" transform="rotate(234)"/>
  <use href="#s2" transform="rotate(270)"/>
  <use href="#s1" transform="rotate(306)"/>
  <use href="#s2" transform="rotate(342)"/>

  <circle r="8" fill="#e0467f" stroke="#4a1d3f" stroke-width="2.6"/>
  <circle r="3.6" fill="#ff86b2"/>
  <circle cx="-2.6" cy="-2.8" r="1.5" fill="#fff"/>
</svg>`;