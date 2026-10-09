(function () {
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const canvas = document.getElementById("bg");
  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5));
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(60, 1, 1, 1000);
  camera.position.z = 260;
  const N = 90, LIMIT = 70, pos = [], vel = [];
  for (let i = 0; i < N; i++) {
    pos.push((Math.random() - .5) * 420, (Math.random() - .5) * 260, (Math.random() - .5) * 220);
    vel.push((Math.random() - .5) * .18, (Math.random() - .5) * .18, (Math.random() - .5) * .18);
  }
  const pGeo = new THREE.BufferGeometry();
  pGeo.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
  const points = new THREE.Points(pGeo, new THREE.PointsMaterial({ color: 0x8fa8ff, size: 2.6, transparent: true, opacity: .9 }));
  const lGeo = new THREE.BufferGeometry();
  const lines = new THREE.LineSegments(lGeo, new THREE.LineBasicMaterial({ color: 0x6f7cff, transparent: true, opacity: .22 }));
  const group = new THREE.Group(); group.add(points, lines); scene.add(group);
  function resize() { renderer.setSize(innerWidth, innerHeight, false); camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); }
  addEventListener("resize", resize); resize();
  let mx = 0, my = 0;
  addEventListener("mousemove", (e) => { mx = (e.clientX / innerWidth - .5) * 2; my = (e.clientY / innerHeight - .5) * 2; });
  (function frame() {
    const p = pGeo.attributes.position.array;
    for (let i = 0; i < N; i++) for (let k = 0; k < 3; k++) {
      p[i*3+k] += vel[i*3+k];
      if (Math.abs(p[i*3+k]) > (k === 0 ? 210 : k === 1 ? 130 : 110)) vel[i*3+k] *= -1;
    }
    pGeo.attributes.position.needsUpdate = true;
    const seg = [];
    for (let i = 0; i < N; i++) for (let j = i + 1; j < N; j++) {
      const dx = p[i*3]-p[j*3], dy = p[i*3+1]-p[j*3+1], dz = p[i*3+2]-p[j*3+2];
      if (dx*dx + dy*dy + dz*dz < LIMIT*LIMIT) seg.push(p[i*3], p[i*3+1], p[i*3+2], p[j*3], p[j*3+1], p[j*3+2]);
    }
    lGeo.setAttribute("position", new THREE.Float32BufferAttribute(seg, 3));
    group.rotation.y += (mx * .35 - group.rotation.y) * .03;
    group.rotation.x += (-my * .2 - group.rotation.x) * .03;
    renderer.render(scene, camera);
    requestAnimationFrame(frame);
  })();
})();