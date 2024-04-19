const fs = require('fs');
const xml2js = require('xml2js');
const { execSync } = require('child_process');
const createCsvWriter = require('csv-writer').createObjectCsvWriter;

async function importXMLData() {
    try {
        const xmlData = fs.readFileSync('data.xml', 'utf8');
        const parsedData = await xml2js.parseStringPromise(xmlData);
        let articles = processArticles(parsedData);
        console.log(articles);

        // Use Supabase CLI to insert data
        // execSync(`supabase db insert your_table_name --file temp_data.csv`);
        // console.log('Data inserted successfully.');
        writeToCSV(articles, 'temp_data.csv')
    } catch (error) {
        console.error('Failed to import XML data:', error);
    }
}

function processArticles(parsedData) {
    const articleList = parsedData.previonxml.articlelist || [];
    const articles = [];

    articleList.forEach((articleEntry) => {
        articleEntry.article.forEach((article) => {
            const title = article.header[0].metadata[1].$.value;
            const content = extractContent(article.body[0].box);

            console.log(title);
            console.log(content);

            articles.push({
                title: title,
                content: content
            });
        });
    });

    return articles;
}

function extractContent(boxes) {
    return boxes.map(box => {
        return box.content[0].paragraph.map(paragraph => {
            return paragraph.character.map(char => char._).join(' ');
        }).join(' ');
    }).join(' ');
}

async function writeToCSV(articles, filePath) {
  const csvWriter = createCsvWriter({
      path: filePath,
      header: [
          {id: 'title', title: 'TITLE'},
          {id: 'content', title: 'CONTENT'}
      ]
  });

  try {
      await csvWriter.writeRecords(articles);
      console.log('The CSV file was written successfully');
  } catch (error) {
      console.error('Error writing CSV file:', error);
  }
}

importXMLData();
