# Lambda layer compile script for a single Python package

BUCKET="lambda-layers-583168578067"
PACKAGE="$1"
TARGET="python"
rm -r "$TARGET"

mkdir "$TARGET"

pip install "$PACKAGE" --target "./$TARGET"
cp -r "$PACKAGE" "$TARGET"
zip -r "$PACKAGE.zip" "$TARGET"

rm -r "$TARGET"


aws s3 cp "$PACKAGE.zip" "s3://$BUCKET/$PACKAGE.zip" --profile personal
rm "$PACKAGE.zip"

