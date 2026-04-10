// 诱导按钮 -> 浮现告白
const btn = document.getElementById('secretBtn');
const msg = document.getElementById('secretMsg');

btn.addEventListener('click', () => {
  // 显示告白文字
  msg.classList.add('show');

  // 按钮变化
  btn.querySelector('span').textContent = '💖 你已发现这个秘密 💖';
  btn.style.animation = 'none';
  btn.style.background = 'linear-gradient(135deg, #fff5e6, #ffe0b2)';

  // 撒爱心
  for (let i = 0; i < 30; i++) {
    setTimeout(() => createHeart(), i * 80);
  }

  // 平滑滚动到告白文字
  setTimeout(() => {
    msg.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }, 200);
});

function createHeart() {
  const heart = document.createElement('div');
  heart.className = 'heart';
  const hearts = ['❤️', '🧡', '💛', '🍊', '✨', '💕'];
  heart.textContent = hearts[Math.floor(Math.random() * hearts.length)];
  heart.style.left = Math.random() * window.innerWidth + 'px';
  heart.style.top = window.innerHeight - 100 + 'px';
  heart.style.fontSize = (20 + Math.random() * 20) + 'px';
  document.body.appendChild(heart);
  setTimeout(() => heart.remove(), 3000);
}

// 滚动时导航栏阴影
const navbar = document.querySelector('.navbar');
window.addEventListener('scroll', () => {
  if (window.scrollY > 30) {
    navbar.style.boxShadow = '0 4px 20px rgba(255,122,0,0.1)';
  } else {
    navbar.style.boxShadow = 'none';
  }
});
