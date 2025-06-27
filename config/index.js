const environment = process.env.NODE_ENV || 'local';
console.log('Loading config for environment:', environment);
const config = (await import(`./${environment}.js`)).default;
export default config;