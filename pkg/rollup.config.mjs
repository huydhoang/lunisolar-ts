import typescript from '@rollup/plugin-typescript';
import resolve from '@rollup/plugin-node-resolve';
import commonjs from '@rollup/plugin-commonjs';
import json from '@rollup/plugin-json';

export default {
  input: 'src/index.ts',
  output: [
    { file: 'dist/index.cjs', format: 'cjs', sourcemap: true, exports: 'named' },
    { file: 'dist/index.mjs', format: 'esm', sourcemap: true }
  ],
  plugins: [
    resolve({ extensions: ['.mjs', '.js', '.json', '.ts'] }),
    commonjs(),
    json(),
    typescript({ tsconfig: './tsconfig.json', declaration: true, declarationDir: 'dist' })
  ]
};
